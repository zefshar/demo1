///https://pub.dev/packages/event
import 'package:event/event.dart';

///
class ResultChangedArgs extends EventArgs {
  int? classNumber;
  String? imageReference;
  bool? remove;

  ResultChangedArgs(this.classNumber, this.imageReference, {this.remove = false});
}
