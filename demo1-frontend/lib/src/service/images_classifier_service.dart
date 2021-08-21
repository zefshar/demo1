import 'dart:collection';

import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/model/download_report_args.dart';
import 'package:demo1/src/model/reset_results_args.dart';
import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/select_class_args.dart';
import 'package:demo1/src/model/select_image_args.dart';
import 'package:demo1/src/model/shared_folder_args.dart';
import 'package:demo1/src/utils.dart';
import 'package:event/event.dart';
import 'package:flutter/src/foundation/key.dart';
import 'package:tuple/tuple.dart';

final DEFAULT_CLASSES_COUNT = 2;
final DEFAULT_COLUMNS_COUNT = 2;

/// Represents a global application state
class ImagesClassifierService {
  int? _classesCount = DEFAULT_CLASSES_COUNT;

  int? _columnsCount = DEFAULT_COLUMNS_COUNT;

  bool? _finishedClassification = false;

  String? _sharedFolder = '';

  Tuple2<String?, Key?>? _selectedImage;

  int? _selectedClass;

  Map<int, Map<Tuple2<String?, Key?>, int>> _classifierResult = LinkedHashMap();

  final classesCountChangedEvent = Event<ClassesCountArgs>();

  final columnsCountChangedEvent = Event<ColumnsCountArgs>();

  final downloadReportEvent = Event<DownloadReportArgs>();

  final sharedFolderChangedEvent = Event<SharedFolderArgs>();

  final resultChangedEvent = Event<ResultChangedArgs>();

  final resetResultsEvent = Event<ResetResultsArgs>();

  final selectImageEvent = Event<SelectImageArgs>();

  final selectClassEvent = Event<SelectClassArgs>();

  set ClassesCount(int? value) {
    final delta = (value ?? this._classesCount ?? 0) - (this._classesCount ?? 0);
    this._classesCount = value;
    this.classesCountChangedEvent.broadcast(ClassesCountArgs(value));
    if (delta < 0) {
      final minimalKey = this._classesCount ?? 0;
      // Remove images from class
      this._classifierResult.entries.forEach((e) {
        if (e.key >= minimalKey) {
          final classifiedImageForKey = Set.of(e.value.keys);
          classifiedImageForKey.forEach((imageReference) {
            this.dropImageFromClass(imageReference, e.key);
          });
        }
      });
    }
  }

  int? get ClassesCount {
    return this._classesCount;
  }

  set ColumnsCount(int? value) {
    this._columnsCount = value;
    this.columnsCountChangedEvent.broadcast(ColumnsCountArgs(value));
  }

  int? get ColumnsCount {
    return this._columnsCount;
  }

  set FinishedClassification(bool? value) {
    this._finishedClassification = value;
    this.downloadReportEvent.broadcast(DownloadReportArgs(value));
  }

  bool? get FinishedClassification {
    return this._finishedClassification;
  }

  set SharedFolder(String? value) {
    this._sharedFolder = value;
    this.sharedFolderChangedEvent.broadcast(SharedFolderArgs(value));
  }

  String? get SharedFolder {
    return this._sharedFolder;
  }

  // @returns (imageReference, imageIndex, className, count)
  Iterable<Tuple4<String?, int?, String?, int?>> get ClassifierResult {
    return this._classifierResult.entries.map((a) => a.value.entries.map((b) => Tuple4(
            b.key.item1,
            (b.key.item2 as ValueKey<int>).value,
            GetExcelColumnName(a.key + 1),
            b.value))).expand((entry) => entry).toList();
  }

  void assignImageToClass(
      Tuple2<String?, Key?> imageReference, int classNumber) {
    if (!this._classifierResult.containsKey(classNumber)) {
      this._classifierResult.putIfAbsent(classNumber, () => LinkedHashMap());
    }
    this._classifierResult[classNumber]!.putIfAbsent(imageReference, () => 0);
    this._classifierResult[classNumber]![imageReference] =
        this._classifierResult[classNumber]![imageReference]! + 1;
    this
        .resultChangedEvent
        .broadcast(ResultChangedArgs(classNumber, imageReference));
  }

  void dropImageFromClass(
      Tuple2<String?, Key?> imageReference, int classNumber) {
    if (!this._classifierResult.containsKey(classNumber)) {
      return;
    }
    if (!this._classifierResult[classNumber]!.containsKey(imageReference)) {
      return;
    }
    if (this._classifierResult[classNumber]![imageReference]! <= 1) {
      this._classifierResult[classNumber]!.remove(imageReference);
    } else {
      this._classifierResult[classNumber]![imageReference] =
          this._classifierResult[classNumber]![imageReference]! - 1;
    }
    this.resultChangedEvent.broadcast(
        ResultChangedArgs(classNumber, imageReference, remove: true));
  }

  void resetResults() {
    this._classifierResult.clear();
    this.resetResultsEvent.broadcast(
        ResetResultsArgs());
  }

  Tuple2<String?, Key?>? get SelectedImage => this._selectedImage;

  set SelectedImage(Tuple2<String?, Key?>? value) {
    final event = Tuple2(value, this._selectedClass);
    if (event.item1 != null && event.item2 != null) {
      this._selectedImage = null;
      this._selectedClass = null;
      this.selectImageEvent.broadcast(SelectImageArgs(null));
      this.selectClassEvent.broadcast(SelectClassArgs(null));
      this.assignImageToClass(event.item1!, event.item2!);
    } else {
      this._selectedImage = value;
      this.selectImageEvent.broadcast(SelectImageArgs(value));
    }
  }

  int? get SelectedClass => this._selectedClass;

  set SelectedClass(int? value) {
    final event = Tuple2(this._selectedImage, value);
    if (event.item1 != null && event.item2 != null) {
      this._selectedImage = null;
      this._selectedClass = null;
      this.selectImageEvent.broadcast(SelectImageArgs(null));
      this.selectClassEvent.broadcast(SelectClassArgs(null));
      this.assignImageToClass(event.item1!, event.item2!);
    } else {
      this._selectedClass = value;
      this.selectClassEvent.broadcast(SelectClassArgs(value));
    }
  }

  int imagesCount(int index) {
    if (!this._classifierResult.containsKey(index) ||
        this._classifierResult[index]!.isEmpty) {
      return 0;
    }
    return this._classifierResult[index]!.values.reduce((x, y) => x + y);
  }

  bool isClassified(Tuple2<String?, Key?> value) {
    return this
        ._classifierResult
        .entries
        .any((element) => element.value.containsKey(value));
  }

  bool areAllKeysHaveClassified(Set<Key> keys) {
    return keys.every((key) => this
        ._classifierResult
        .entries
        .any((entry) => entry.value.keys.any((tuple) => tuple.item2 == key)));
  }

  void dropLastImageFromClass(int value) {
    if (this._classifierResult.containsKey(value) &&
        this._classifierResult[value]!.isNotEmpty) {
      final lastImage = this._classifierResult[value]?.keys.last;
      this.dropImageFromClass(lastImage!, value);
    }
  }

  String? lastImageForClass(int value) {
    if (this._classifierResult.containsKey(value) &&
        this._classifierResult[value]!.isNotEmpty) {
      return this._classifierResult[value]?.keys.last.item1;
    }
    return null;
  }

  Iterable<Tuple2<String?, Key?>>? lastTwoImagesForClass(int value) {
    if (this._classifierResult.containsKey(value) &&
        this._classifierResult[value]!.length > 1) {
      return this._classifierResult[value]?.keys.skip(this._classifierResult[value]!.length - 2);
    }
    return null;
  }
}
