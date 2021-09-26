import 'package:demo1/src/component/compare_images_dialog.dart';
import 'package:demo1/src/model/reset_results_args.dart';
import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/select_class_args.dart';
import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:demo1/src/utils.dart';
import 'package:flutter/material.dart';

/// Image class representation
class ImagesClassCardWidget extends StatefulWidget {
  final int index;
  final ImagesClassifierService imagesClassifierService;

  const ImagesClassCardWidget(
      {required this.index, required this.imagesClassifierService, Key? key})
      : super(key: key);

  @override
  _ImagesClassCardWidgetState createState() => _ImagesClassCardWidgetState();

  int value() {
    return this.index;
  }
}

class _ImagesClassCardWidgetState extends State<ImagesClassCardWidget> {
  int count = 0;
  late bool _selected;
  late String? _lastImageUrl;

  @override
  void initState() {
    super.initState();
    this._selected =
        (this.widget.imagesClassifierService.SelectedImage?.item2 as ValueKey)
                .value ==
            this.widget.value();

    this._lastImageUrl = this
        .widget
        .imagesClassifierService
        .lastImageForClass(this.widget.value());

    // Subscriptions
    this
        .widget
        .imagesClassifierService
        .resultChangedEvent
        .subscribe(this.resultIsChanged);
    this
        .widget
        .imagesClassifierService
        .resetResultsEvent
        .subscribe(this.resetResults);
    handleSelected();
  }

  @override
  void dispose() {
    disableListening();
    this
        .widget
        .imagesClassifierService
        .resultChangedEvent
        .unsubscribe(this.resultIsChanged);
    this
        .widget
        .imagesClassifierService
        .resetResultsEvent
        .unsubscribe(this.resetResults);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: GestureDetector(
        onTap: () {
          setState(() {
            this._selected = !this._selected;
            this.widget.imagesClassifierService.SelectedClass =
                this._selected ? this.widget.index : null;
            handleSelected();
          });
        },
        onDoubleTap: this.dropLastImage,
        child: Card(
            child: Center(
                child: Stack(children: [
          Column(
            mainAxisAlignment: MainAxisAlignment.start,
            mainAxisSize: MainAxisSize.max,
            children: <Widget>[
              Padding(
                padding: EdgeInsets.fromLTRB(6, 0, 0, 0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: <Widget>[
                    Text(
                      'CLASS ',
                      style: TextStyle(
                          fontSize: 18,
                          fontFamily: 'TexGyreHeros',
                          color: Color(0xFFD7BBFA)),
                    ),
                    Text(
                      '${GetExcelColumnName(widget.index + 1)}',
                      style: TextStyle(
                          fontSize: 18,
                          fontFamily: 'TexGyreHeros',
                          color: Colors.black87),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'IMAGES: ',
                      style: TextStyle(
                          fontSize: 18,
                          fontFamily: 'TexGyreHeros',
                          color: Color(0xFFD7BBFA)),
                    ),
                    Text(
                      '${this.count}',
                      style: TextStyle(
                          fontSize: 20,
                          fontFamily: 'TexGyreHeros',
                          color: Colors.black45,
                          fontWeight: FontWeight.w900,
                          decoration: TextDecoration.underline,
                          decorationStyle: TextDecorationStyle.solid,
                          decorationColor: Color(0xFFD7BBFA)),
                    ),
                    const SizedBox(width: 8),
                  ],
                ),
              ),
              Padding(
                  padding: EdgeInsets.fromLTRB(0, 0, 22, 4),
                  child: Container(
                      height: 159,
                      width: 159,
                      alignment: Alignment.center,
                      child: Image(
                        fit: BoxFit.contain,
                        image: NetworkImage(
                            (this._lastImageUrl ?? '').isEmpty
                                ? 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
                                : this._lastImageUrl!,
                            scale: 0.1),
                      ))),
            ],
          ),
          Positioned(
            right: 13,
            bottom: 13,
            child: Opacity(
              opacity: this._selected ? 1.0 : 0.0,
              child: Icon(
                Icons.check_circle,
                color: Colors.black.withOpacity(0.5),
                size: 42.0,
              ),
            ),
          ),
          Positioned(
            right: 13,
            bottom: 73,
            child: GestureDetector(
              onTap: this.compareLastTwoImages,
              child: Opacity(
                opacity: this.count > 1 ? 1.0 : 0.0,
                child: Icon(
                  Icons.compare_sharp,
                  color: Colors.black.withOpacity(0.5),
                  size: 42.0,
                ),
              ),
            ),
          ),
          Positioned(
            right: 13,
            top: 23,
            child: GestureDetector(
              onTap: this.dropLastImage,
              child: Opacity(
                opacity: (this._lastImageUrl ?? '').isNotEmpty ? 1.0 : 0.0,
                child: Icon(
                  Icons.clear,
                  color: Colors.black.withOpacity(0.5),
                  size: 42.0,
                ),
              ),
            ),
          ),
        ]))),
      ),
    );
  }

  void dropLastImage() {
    this
        .widget
        .imagesClassifierService
        .dropLastImageFromClass(this.widget.value());
  }

  void compareLastTwoImages() async {
    final imageReferences = this
        .widget
        .imagesClassifierService
        .lastTwoImagesForClass(this.widget.value());
    if (imageReferences != null) {
      final imageUrls = imageReferences.toList();
      await showDialog(
          context: context,
          builder: (_) => CompareImagesDialog(
              GetExcelColumnName(widget.index + 1),
              imageUrls[0],
              imageUrls[1]));
    }
  }

  void resultIsChanged(ResultChangedArgs? args) {
    if (args != null && args.classNumber == this.widget.index) {
      this.setState(() {
        this.count =
            this.widget.imagesClassifierService.imagesCount(this.widget.index);
        this._selected = this.widget.imagesClassifierService.SelectedImage ==
            this.widget.value();

        this._lastImageUrl = this
            .widget
            .imagesClassifierService
            .lastImageForClass(this.widget.value());
      });
    }
  }

  void resetResults(ResetResultsArgs? args) {
    this.setState(() {
      this.count = 0;
      this._selected = false;

      this._lastImageUrl = null;
    });
  }

  void handleSelected() {
    if (this._selected) {
      this
          .widget
          .imagesClassifierService
          .selectClassEvent
          .subscribe(this.selectImageHandler);
    } else {
      disableListening();
    }
  }

  void selectImageHandler(args) {
    if (args is SelectClassArgs && ((args).value != widget.value())) {
      disableListening();
      setState(() {
        this._selected = false;
      });
    }
  }

  void disableListening() {
    this
        .widget
        .imagesClassifierService
        .selectClassEvent
        .unsubscribe(this.selectImageHandler);
  }
}
