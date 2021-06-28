import 'package:demo1/src/component/app_bar_title_widget.dart';
import 'package:demo1/src/component/gallery_toolbar_widget.dart';
import 'package:demo1/src/component/image_card_widget.dart';
import 'package:demo1/src/model/classes_count_args.dart';
import 'package:demo1/src/model/columns_count_args.dart';
import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

void main() {
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
  @override
  Widget build(BuildContext context) {
    widget.imagesClassifierService.classesCountChangedEvent.subscribe((args) {
      if (args is ClassesCountArgs) {
        this.setState(() {});
      }
    });

    widget.imagesClassifierService.columnsCountChangedEvent.subscribe((args) {
      if (args is ColumnsCountArgs && ((args).value ?? 0) > 0) {
        this.setState(() {});
      }
    });

    var classes = List<Widget>.generate(
        this.widget.imagesClassifierService.ClassesCount ?? 0,
        (int index) => ImageCardWidget(
              index: index,
            ));

    var scaffold = Scaffold(
      appBar: AppBar(
        title: AppBarTitleWidget(
            title: widget.title,
            imagesClassifierService: widget.imagesClassifierService),
        elevation: 1,
      ),
      body: Container(
          child: Column(children: [
        Flexible(
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
          child: Container(
            constraints:
                BoxConstraints(maxHeight: 62, minWidth: double.infinity),
            child: GalleryToolbarWidget(
                imagesClassifierService: widget.imagesClassifierService),
          ),
        ),
        Expanded(
          child: GridView.count(
            crossAxisCount: widget.imagesClassifierService.ColumnsCount ?? 0,
            // Generate 100 widgets that display their index in the List.
            children: List.generate(100, (index) {
              return Center(
                child: Text(
                  'Item $index',
                  style: Theme.of(context).textTheme.headline5,
                ),
              );
            }),
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
}
