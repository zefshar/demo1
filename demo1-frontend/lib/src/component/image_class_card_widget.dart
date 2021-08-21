import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/select_class_args.dart';
import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:demo1/src/utils.dart';
import 'package:flutter/material.dart';

/// Image class representation
class ImageClassCardWidget extends StatefulWidget {
  final int index;
  final ImagesClassifierService imagesClassifierService;

  const ImageClassCardWidget(
      {required this.index, required this.imagesClassifierService, Key? key})
      : super(key: key);

  @override
  _ImageClassCardWidgetState createState() => _ImageClassCardWidgetState();

  int value() {
    return this.index;
  }
}

class _ImageClassCardWidgetState extends State<ImageClassCardWidget> {
  int count = 0;
  late bool _selected;
  late String? _lastImageUrl;

  @override
  void initState() {
    super.initState();
    this._selected = this.widget.imagesClassifierService.SelectedImage ==
        this.widget.value();

    this._lastImageUrl = this
        .widget
        .imagesClassifierService
        .lastImageForClass(this.widget.value());
    this
        .widget
        .imagesClassifierService
        .resultChangedEvent
        .subscribe(this.resultIsChanged);
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
        onDoubleTap: () {
          this
              .widget
              .imagesClassifierService
              .dropLastImageFromClass(this.widget.value());
        },
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
                      alignment: Alignment.topLeft,
                      child: Image(
                        fit: BoxFit.fitWidth,
                        image: NetworkImage((this._lastImageUrl ?? '').isEmpty
                            ? 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
                            : this._lastImageUrl!),
                      ))),
            ],
          ),
          Positioned(
            right: 13,
            top: 13,
            child: Opacity(
              opacity: this._selected ? 1.0 : 0.0,
              child: Icon(
                Icons.check_circle,
                color: Colors.black.withOpacity(0.5),
                size: 42.0,
              ),
            ),
          ),
        ]))),
      ),
    );
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
