
import 'package:demo1/src/model/classes_count_args.dart';
import 'package:event/event.dart';

final DEFAULT_CLASSES_COUNT = 7;

/// Represents a global application state
class ImagesClassifierService {

  int? _classesCount = DEFAULT_CLASSES_COUNT;

  final classesCountChangedEvent = Event<ClassesCountArgs>();

  set ClassesCount (int? value) {
    this._classesCount = value;
    this.classesCountChangedEvent.broadcast(ClassesCountArgs(value));
  }

  int? get ClassesCount {
    return _classesCount;
  }

}