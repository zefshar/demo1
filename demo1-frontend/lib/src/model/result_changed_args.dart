///https://pub.dev/packages/event
import 'package:event/event.dart';
import 'package:flutter/widgets.dart';
import 'package:tuple/tuple.dart';

///
class ResultChangedArgs extends EventArgs {
  int classNumber;
  Tuple2<String?, Key?> imageReference;
  bool remove;

  ResultChangedArgs(this.classNumber, this.imageReference, {this.remove = false});
}
