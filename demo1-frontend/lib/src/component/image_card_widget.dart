import 'package:demo1/src/model/result_changed_args.dart';
import 'package:demo1/src/model/select_image_args.dart';
import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:tuple/tuple.dart';

/// Image representation
class ImageCardWidget extends StatefulWidget {
  final String? imageReference;
  final ImagesClassifierService imagesClassifierService;

  const ImageCardWidget(
      {required this.imageReference,
      required this.imagesClassifierService,
      Key? key})
      : super(key: key);

  @override
  _ImageCardWidgetState createState() => _ImageCardWidgetState();

  Tuple2<String?, Key?> value() {
    return Tuple2(this.imageReference, this.key);
  }
}

class _ImageCardWidgetState extends State<ImageCardWidget> {
  late bool _selected;
  late bool _isBlank;

  @override
  void initState() {
    super.initState();
    this._selected = this.widget.imagesClassifierService.SelectedImage ==
        this.widget.value();
    this._isBlank =
        this.widget.imagesClassifierService.isClassified(this.widget.value());
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
    return GestureDetector(
      onTap: () {
        if (!this._isBlank) {
          setState(() {
            this._selected = !this._selected;
            this.widget.imagesClassifierService.SelectedImage =
                this._selected ? this.widget.value() : null;
            handleSelected();
          });
        }
      },
      child: Card(
          elevation: this._selected ? 13.0 : 0.0,
          shadowColor: Theme.of(context).backgroundColor,
          shape:
              const ContinuousRectangleBorder(borderRadius: BorderRadius.zero),
          child: Opacity(
            opacity: this._isBlank ? 0.0 : 1.0,
            child: Stack(
              children: [
                Center(
                    child: Image(
                  fit: BoxFit.contain,
                  image: NetworkImage(
                      (this.widget.imageReference ?? '').isEmpty
                          ? 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
                          : this.widget.imageReference!,
                      scale: 0.1),
                )),
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
                Positioned(
                  left: 13,
                  top: 13,
                  child: Text(this.widget.key?.toString() ?? ''),
                )
              ],
            ),
          )),
    );
  }

  void resultIsChanged(ResultChangedArgs? args) {
    if (args != null && args.imageReference == this.widget.value()) {
      this.setState(() {
        this._selected = this.widget.imagesClassifierService.SelectedImage ==
            this.widget.value();
        this._isBlank = !args.remove!;
      });
    }
  }

  void handleSelected() {
    if (this._selected) {
      this
          .widget
          .imagesClassifierService
          .selectImageEvent
          .subscribe(this.selectImageHandler);
    } else {
      disableListening();
    }
  }

  void selectImageHandler(args) {
    if (args is SelectImageArgs && ((args).value != widget.value())) {
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
        .selectImageEvent
        .unsubscribe(this.selectImageHandler);
  }
}
