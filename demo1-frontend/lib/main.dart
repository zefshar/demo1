import 'dart:convert';

import 'package:demo1/src/component/classification_results_title_widget.dart';
import 'package:demo1/src/component/gallery_toolbar_widget.dart';
import 'package:demo1/src/component/image_card_widget.dart';
import 'package:demo1/src/component/image_class_card_widget.dart';
import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/model/download_report_args.dart';
import 'package:demo1/src/model/google_drive_link.dart';
import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/shared_folder_args.dart';
import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:excel/excel.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
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
          title: '<Classification results file name>',
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
  late List<Tuple2<String?, Key?>> unclassifiedImages;

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

    this.unclassifiedImages = List.generate(
        100,
        (index) => Tuple2(
            'https://flutter.github.io/assets-for-api-docs/assets/widgets/owl.jpg',
            ValueKey(index)));

    this.widget.imagesClassifierService.resultChangedEvent.subscribe((args) {
      // Remove blank row
      final columnsCount = this.widget.imagesClassifierService.ColumnsCount!;
      if (args is ResultChangedArgs && columnsCount > 0) {
        final index = (args.imageReference.item2 as ValueKey).value as int;
        final int lowerBound = (index ~/ columnsCount) * columnsCount;
        final rowKeys = Set<Key>.from(List<Key>.generate(
            columnsCount, (index) => ValueKey(lowerBound + index)));
        if (!args.remove &&
            this
                .widget
                .imagesClassifierService
                .areAllKeysHaveClassified(rowKeys)) {
          this.setState(() {
            this
                .unclassifiedImages
                .removeWhere((element) => rowKeys.contains(element.item2));
          });
        }
        if (args.remove) {
          final upperIndex = this.unclassifiedImages.indexWhere(
              (element) => (element.item2 as ValueKey<int>).value >= index);
          // If indexes are equals replace image url
          if (this.unclassifiedImages[upperIndex].item2 ==
              args.imageReference.item2) {
            this.setState(() {
              this.unclassifiedImages[upperIndex] = args.imageReference;
            });
          } else {
            // Else insert row
            final rowOfImageReferences = List<Tuple2<String?, Key?>>.generate(
                columnsCount,
                (i) => Tuple2(
                    (lowerBound + i) == index
                        ? args.imageReference.item1
                        : null,
                    ValueKey(lowerBound + i)));
            this.setState(() {
              if (upperIndex > 0) {
                this
                    .unclassifiedImages
                    .insertAll(upperIndex, rowOfImageReferences);
              } else if (upperIndex == 0) {
                this.unclassifiedImages.insertAll(0, rowOfImageReferences);
              } else {
                // Not found case
                this.unclassifiedImages.addAll(rowOfImageReferences);
              }
            });
          }
        }
      }
    });

    this
        .widget
        .imagesClassifierService
        .sharedFolderChangedEvent
        .subscribe((args) {
      if (args is SharedFolderArgs) {
        this.isValidShardFolder(args.value!).then((value) {
          if (value) {
            final folderId = GoogleDriveLink.getFolderId(args.value!);
            print('There is valid shared folder ${folderId}');
            this.requestImageLinks(folderId).then((imageLinks) {
              final fullLinks = imageLinks.asMap().entries.map((e) => Tuple2(
                  'https://drive.google.com/uc?id=${e.value}',
                  ValueKey(e.key)));
              setState(() {
                this.unclassifiedImages.clear();
                this.unclassifiedImages.addAll(fullLinks);
                this.widget.imagesClassifierService.resetResults();
              });
            });
          } else {
            print('Can\'t find correct shared folder-id in ${args.value}');
          }
        });
      }
    });

    this.widget.imagesClassifierService.resetResultsEvent.subscribe((args) {
      // Nothing do
    });
  }

  @override
  void dispose() {
    this
        .widget
        .imagesClassifierService
        .classesCountChangedEvent
        .unsubscribeAll();
    this.widget.imagesClassifierService.downloadReportEvent.unsubscribeAll();
    this
        .widget
        .imagesClassifierService
        .sharedFolderChangedEvent
        .unsubscribeAll();
    this.widget.imagesClassifierService.resultChangedEvent.unsubscribeAll();
    this.widget.imagesClassifierService.resetResultsEvent.unsubscribeAll();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    var classes = List<Widget>.generate(
        this.widget.imagesClassifierService.ClassesCount ?? 0,
        (int index) => ImageClassCardWidget(
            index: index,
            imagesClassifierService: this.widget.imagesClassifierService));

    final imagesForClassification = this
        .unclassifiedImages
        .map((e) => ImageCardWidget(
              imageReference: e.item1,
              imagesClassifierService: this.widget.imagesClassifierService,
              key: e.item2,
            ))
        .toList();

    var scaffold = Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        title: ClassificationResultsTitleWidget(
            title: widget.title,
            imagesClassifierService: widget.imagesClassifierService),
        elevation: 1,
      ),
      body: Container(
          child: Column(children: [
        Container(
          constraints: BoxConstraints(
              maxHeight: 200, minHeight: 200, minWidth: double.infinity),
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: classes,
          ),
        ),
        Container(
          constraints: BoxConstraints(maxHeight: 62, minWidth: double.infinity),
          child: GalleryToolbarWidget(
              imagesClassifierService: widget.imagesClassifierService),
        ),
        Expanded(
            child: GridView.count(
          crossAxisCount: widget.imagesClassifierService.ColumnsCount ?? 0,
          // Generate 100 widgets that display their index in the List.
          children: imagesForClassification,
        )),
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
    this.widget.imagesClassifierService.ClassifierResult.forEach((element) {
      table.appendRow(element.toList());
    });

    final bytes = excel.encode();

    return bytes!;
  }

  Future<bool> isValidShardFolder(String value) async {
    try {
      final folderId = Uri.parse(value).isAbsolute
          ? GoogleDriveLink.getFolderId(value)
          : value;
      // // TODO: fix requests (There were block by CORS policy)
      // final folderLink = 'https://drive.google.com/drive/folders/$folderId';

      // final response = await http.get(Uri.parse(folderLink), headers: {
      //   'Accept': '*/*',
      //   'Access-Control-Allow-Origin': '*',
      //   'Access-Control-Allow-Headers': '*',
      // });
      // return Future.value(response.body.contains('"$folderId"'));
      return Future.value(folderId.isNotEmpty);
    } catch (e) {
      print('Error: $e');
      return Future.value(false);
    }
  }

  Future<List<String>> requestImageLinks(String folderId) async {
    try {
      var apiEndpoint = const String.fromEnvironment('API_ENDPOINT',
          defaultValue: '/demo1/api');
      return http.get(Uri.parse('$apiEndpoint/files?$folderId'), headers: {
        'Accept': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
      }).then((response) {
        Map jsonData = json.decode(response.body) as Map;
        final List<String> links = jsonData['files']
            .map((element) => element['id'])
            .toList()
            .cast<String>();
        return links;
      }).onError((error, stackTrace) {
        print('Error: $error');
        return [];
      });
    } catch (e) {
      print('Error: $e');
      return Future.value([]);
    }
  }
}
