import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/model/download_report_args.dart';
import 'package:event/event.dart';

final DEFAULT_CLASSES_COUNT = 2;
final DEFAULT_COLUMNS_COUNT = 2;

/// Represents a global application state
class ImagesClassifierService {
  int? _classesCount = DEFAULT_CLASSES_COUNT;

  int? _columnsCount = DEFAULT_COLUMNS_COUNT;

  bool? _finishedClassification = false;

  final classesCountChangedEvent = Event<ClassesCountArgs>();

  final columnsCountChangedEvent = Event<ColumnsCountArgs>();

  final downloadReportEvent = Event<DownloadReportArgs>();

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
}
