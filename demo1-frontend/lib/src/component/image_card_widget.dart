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

  void refresh() {
  }
}

class _ImageCardWidgetState extends State<ImageCardWidget> {
  bool _selected = false;

  @override
  void initState() {
    super.initState();
    
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
        onTap: () {
          setState(() {
            this._selected = !this._selected;
            if (this._selected) {
              this.widget.imagesClassifierService.SelectedImage = Tuple2(this.widget.imageReference, this.widget.key);
            }
          });
        },
        child: Card(
            elevation: this._selected ? 13.0 : 0.0,
            shadowColor: Theme.of(context).backgroundColor,
            shape: const ContinuousRectangleBorder(
                borderRadius: BorderRadius.zero),
            child: Center(
              child: Stack(
                children: [
                  Image(
                    fit: BoxFit.fitWidth,
                    image: NetworkImage(this.widget.imageReference!),
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
                  )
                ],
              ),
            )));
  }
}
