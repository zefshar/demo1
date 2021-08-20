import 'package:demo1/src/component/app_bar_title_widget.dart';
import 'package:demo1/src/component/gallery_toolbar_widget.dart';
import 'package:demo1/src/component/image_card_widget.dart';
import 'package:demo1/src/component/image_class_card_widget.dart';
import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/model/download_report_args.dart';
import 'package:demo1/src/model/select_image_args.dart';
import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:excel/excel.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:tuple/tuple.dart';
//import 'package:pdf/widgets.dart' as pw;
import 'package:universal_html/html.dart' as html;

void main() async {
  runApp(Demo1());
}

class Demo1 extends StatelessWidget {
  static const MaterialColor demo1PrimaryColor = MaterialColor(
    _demo1ColorPrimaryValue,
    <int, Color>{
      50: Color(0xFFF0E4FD),
      100: Color(_demo1ColorPrimaryValue),
      200: Color(0xFFBB90F1),
      300: Color(0xFF9D67E3),
      400: Color(0xFF8749D9),
      500: Color(0xFF712FCE),
      600: Color(0xFF5F2DC7),
      700: Color(0xFF442ABE),
      800: Color(0xFF2427B5),
      900: Color(0xFF0021A5),
    },
  );
  static const int _demo1ColorPrimaryValue = 0xFFD7BBFA;

  static const MaterialColor demo1SecondaryColor = MaterialColor(
    _demo1ColorSecondaryValue,
    <int, Color>{
      50: Color(0xFFF7FEEE),
      100: Color(0xFFEBFCD5),
      200: Color(_demo1ColorSecondaryValue),
      300: Color(0xFFD0F79F),
      400: Color(0xFFC3F397),
      500: Color(0xFFB8F071),
      600: Color(0xFFA7DE68),
      700: Color(0xFF91C85C),
      800: Color(0xFF7DB352),
      900: Color(0xFF5A9040),
    },
  );
  static const int _demo1ColorSecondaryValue = 0xFFDEFABB;

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        FocusScopeNode currentFocus = FocusScope.of(context);

        if (!currentFocus.hasPrimaryFocus) {
          currentFocus.unfocus();
        }
      },
      child: MaterialApp(
        title: 'Image classifier',
        theme: ThemeData(
            primarySwatch: demo1PrimaryColor,
            accentColor: demo1SecondaryColor,
            visualDensity: VisualDensity.adaptivePlatformDensity,
            fontFamily: 'TexGyreHeros'),
        home: HomePage(
          title: 'Image classifier',
          imagesClassifierService: ImagesClassifierService(),
        ),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  HomePage(
      {Key? key, required this.title, required this.imagesClassifierService})
      : super(key: key);

  final String title;
  final ImagesClassifierService imagesClassifierService;

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late List<ImageCardWidget> unclassifiedImages;

  @override
  void initState() {
    super.initState();

    this
        .widget
        .imagesClassifierService
        .classesCountChangedEvent
        .subscribe((args) {
      if (args is ClassesCountArgs) {
        this.setState(() {});
      }
    });

    this
        .widget
        .imagesClassifierService
        .columnsCountChangedEvent
        .subscribe((args) {
      if (args is ColumnsCountArgs && ((args).value ?? 0) > 0) {
        this.setState(() {});
      }
    });

    this
        .widget
        .imagesClassifierService
        .downloadReportEvent
        .subscribe((args) async {
      if (args is DownloadReportArgs) {
        try {
          final bytes =
              this.generateReport(await rootBundle.load('assets/output.xlsx'));
          final blob = html.Blob([
            bytes
          ], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
          final url = html.Url.createObjectUrlFromBlob(blob);
          final anchor = html.AnchorElement(href: url)
            ..setAttribute('download', 'Image-Classifier-Result.xlsx');
          html.document.body?.append(anchor);

          WidgetsBinding.instance?.addPostFrameCallback((_) {
            setState(() {
              anchor.click();
              anchor.remove();
              html.Url.revokeObjectUrl(url);
            });
          });
        } catch (e) {
          print('(Fail) widget.imagesClassifierService.downloadReportEvent');
          print(e);
        }
      }
    });

    this.widget.imagesClassifierService.selectImageEvent.subscribe((args) {
      if (args is SelectImageArgs && ((args).value != null)) {
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    var classes = List<Widget>.generate(
        this.widget.imagesClassifierService.ClassesCount ?? 0,
        (int index) => ImageClassCardWidget(
            index: index,
            imagesClassifierService: this.widget.imagesClassifierService));

    final size = MediaQuery.of(context).size;

    this.unclassifiedImages = List.generate(100, (index) {
      return ImageCardWidget(
        imageReference:
            'https://flutter.github.io/assets-for-api-docs/assets/widgets/owl.jpg',
        imagesClassifierService: this.widget.imagesClassifierService,
        key: UniqueKey(),
      );
    });

    var scaffold = Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        title: AppBarTitleWidget(
            title: widget.title,
            imagesClassifierService: widget.imagesClassifierService),
        elevation: 1,
      ),
      body: Container(
          child: Column(children: [
        Flexible(
          flex: 2,
          child: Container(
            constraints:
                BoxConstraints(maxHeight: 200, minWidth: double.infinity),
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: classes,
            ),
          ),
        ),
        Flexible(
          flex: 1,
          child: Container(
            constraints:
                BoxConstraints(maxHeight: 62, minWidth: double.infinity),
            child: GalleryToolbarWidget(
                imagesClassifierService: widget.imagesClassifierService),
          ),
        ),
        Expanded(
          flex: 3,
          child: GridView.count(
            crossAxisCount: widget.imagesClassifierService.ColumnsCount ?? 0,
            // Generate 100 widgets that display their index in the List.
            children: this.unclassifiedImages,
          ),
        ),
      ])),
    );

    if (kDebugMode) {
      return Banner(
          location: BannerLocation.bottomEnd,
          color: Colors.green,
          message: '\u{1F525}\u{1F525}\u{1F525}\u{1F525}\u{1F525}\u{1F525}',
          child: scaffold);
    }
    return scaffold;
  }

  List<int> generateReport(ByteData data) {
    var excel = Excel.decodeBytes(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes));

    var table = excel.tables.entries.first.value;
    table.appendRow(['image1.jpg', 'A']);
    table.appendRow(['image2.jpg', 'B']);
    table.appendRow(['image3.jpg', '']);

    final bytes = excel.encode();

    return bytes!;
  }
}
