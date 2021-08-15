///https://pub.dev/packages/event
import 'package:event/event.dart';
import 'package:flutter/widgets.dart';
import 'package:tuple/tuple.dart';

///
class SelectImageArgs extends EventArgs {
  Tuple2<String?, Key?>? value;

  SelectImageArgs(this.value);
}
