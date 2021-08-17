import 'dart:collection';

import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/model/download_report_args.dart';
import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/select_class_args.dart';
import 'package:demo1/src/model/select_image_args.dart';
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

  int? _selectedClass;

  Map<int, Map<String, int>> _result = LinkedHashMap();

  final classesCountChangedEvent = Event<ClassesCountArgs>();

  final columnsCountChangedEvent = Event<ColumnsCountArgs>();

  final downloadReportEvent = Event<DownloadReportArgs>();

  final sharedFolderChangedEvent = Event<SharedFolderArgs>();

  final resultChangedEvent = Event<ResultChangedArgs>();

  final selectImageEvent = Event<SelectImageArgs>();

  final selectClassEvent = Event<SelectClassArgs>();

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

  Map<int, List<String>>? get Result {
    return this._result.map((key, value) =>
        MapEntry(key, value.entries.map((entry) => entry.key).toList()));
  }

  void assignImageToClass(String imageReference, int classNumber) {
    if (!this._result.containsKey(classNumber)) {
      this._result.putIfAbsent(classNumber, () => LinkedHashMap());
    }
    this._result[classNumber]!.putIfAbsent(imageReference, () => 0);
    this._result[classNumber]![imageReference] =
        this._result[classNumber]![imageReference]! + 1;
    this
        .resultChangedEvent
        .broadcast(ResultChangedArgs(classNumber, imageReference));
  }

  void dropImageFromClass(String imageReference, int classNumber) {
    if (!this._result.containsKey(classNumber)) {
      return;
    }
    if (!this._result[classNumber]!.containsKey(imageReference)) {
      return;
    }
    if (this._result[classNumber]![imageReference]! <= 1) {
      this._result[classNumber]!.remove(imageReference);
    } else {
      this._result[classNumber]![imageReference] =
          this._result[classNumber]![imageReference]! - 1;
    }
    this
        .resultChangedEvent
        .broadcast(ResultChangedArgs(classNumber, imageReference, remove: true));
  }

  set SelectedImage(Tuple2<String?, Key?>? value) {
    this._selectedImage = value;
    this.selectImageEvent.broadcast(SelectImageArgs(value));
  }

  Tuple2<String?, Key?>? get SelectedImage => this._selectedImage;

  set SelectedClass(int? value) {
    this._selectedClass = value;
    this.selectClassEvent.broadcast(SelectClassArgs(value));
  }

  int? get SelectedClass => this._selectedClass;
}
