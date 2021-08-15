import 'dart:collection';

import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/model/download_report_args.dart';
import 'package:demo1/src/model/result_changed_args%20copy.dart';
import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/shared_folder_args.dart';
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
  List<Tuple2<String?, Key?>> _allSelectedImages = List.empty(growable: true);

  Map<String, Map<String, int>> _result = LinkedHashMap();

  final classesCountChangedEvent = Event<ClassesCountArgs>();

  final columnsCountChangedEvent = Event<ColumnsCountArgs>();

  final downloadReportEvent = Event<DownloadReportArgs>();

  final sharedFolderChangedEvent = Event<SharedFolderArgs>();

  final resultChangedEvent = Event<ResultChangedArgs>();

  final selectImageEvent = Event<SelectImageArgs>();

  set ClassesCount(int? value) {
    this._classesCount = value;
    this.classesCountChangedEvent.broadcast(ClassesCountArgs(value));
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

  Map<String, List<String>>? get Result {
    return this._result.map((key, value) =>
        MapEntry(key, value.entries.map((entry) => entry.key).toList()));
  }

  void assignImageToClass(String imageReference, String className) {
    if (!this._result.containsKey(className)) {
      this._result.putIfAbsent(className, () => LinkedHashMap());
    }
    this._result[className]!.putIfAbsent(imageReference, () => 0);
    this._result[className]![imageReference] =
        this._result[className]![imageReference]! + 1;
    this
        .resultChangedEvent
        .broadcast(ResultChangedArgs(className, imageReference));
  }

  void dropImageFromClass(String imageReference, String className) {
    if (!this._result.containsKey(className)) {
      return;
    }
    if (!this._result[className]!.containsKey(imageReference)) {
      return;
    }
    if (this._result[className]![imageReference]! <= 1) {
      this._result[className]!.remove(imageReference);
    } else {
      this._result[className]![imageReference] =
          this._result[className]![imageReference]! - 1;
    }
    this
        .resultChangedEvent
        .broadcast(ResultChangedArgs(className, imageReference, remove: true));
  }

  set SelectedImage(Tuple2<String?, Key?> value) {
    this._selectedImage = value;
    this._allSelectedImages.add(value);
    this.selectImageEvent.broadcast(SelectImageArgs(value));
  }

  get AllSelectedImages => List.of(this._allSelectedImages);

  void removeFromAllSelectedImages(List<Tuple2<String?, Key?>> values) {
    // TODO: optimize it
    values.forEach((element) {
      this._allSelectedImages.remove(element);
    });
  }
}
