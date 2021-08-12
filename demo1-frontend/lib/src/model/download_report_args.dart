///https://pub.dev/packages/event
import 'package:event/event.dart';

///
class DownloadReportArgs extends EventArgs {
  bool? value;

  DownloadReportArgs(this.value);
}
