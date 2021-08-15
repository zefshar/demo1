///https://pub.dev/packages/event
import 'package:event/event.dart';

///
class ResultChangedArgs extends EventArgs {
  String? className;
  String? imageReference;
  bool? remove;

  ResultChangedArgs(this.className, this.imageReference, {this.remove = false});
}
