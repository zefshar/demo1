import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:tuple/tuple.dart';

class CompareImagesDialog extends StatelessWidget {
  final String classLabel;
  final Tuple2<String?, Key?> oldImageReference;
  final Tuple2<String?, Key?> newImageReference;

  CompareImagesDialog(
      this.classLabel, this.oldImageReference, this.newImageReference);

  @override
  Widget build(BuildContext context) {
    return Dialog(
        child: Stack(children: [
      Row(
        children: [
          Flexible(
              child: Stack(children: [
            Container(
              decoration: BoxDecoration(
                  image: DecorationImage(
                      image: NetworkImage(this.oldImageReference.item1 ??
                          'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='),
                      fit: BoxFit.cover)),
            ),
            Positioned(
              left: 13,
              top: 13,
              child: Text(this.oldImageReference.item2?.toString() ?? ''),
            )
          ])),
          Flexible(
            child: Stack(children: [
              Container(
                decoration: BoxDecoration(
                    image: DecorationImage(
                        image: NetworkImage(this.newImageReference.item1 ??
                            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='),
                        fit: BoxFit.cover)),
              ),
              Positioned(
                left: 13,
                top: 13,
                child: Text(this.newImageReference.item2?.toString() ?? ''),
              )
            ]),
          ),
        ],
      ),
      Positioned(
        right: 48.0,
        child: Opacity(
          opacity: 0.7,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(2.0), //or 15.0
            child: Container(
              height: 42.0,
              width: 62.0,
              color: Colors.white,
              child: Align(
                alignment: Alignment.center,
                child: Text(
                  'Class ${this.classLabel}',
                  style: const TextStyle(color: Colors.black45),
                ),
              ),
            ),
          ),
        ),
      ),
      Positioned(
        right: 0.0,
        child: GestureDetector(
          onTap: () {
            Navigator.of(context).pop();
          },
          child: Opacity(
            opacity: 0.7,
            child: Align(
              alignment: Alignment.topRight,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(2.0), //or 15.0
                child: Container(
                  height: 42.0,
                  width: 42.0,
                  color: Colors.white,
                  child: Icon(Icons.close, color: Colors.black45),
                ),
              ),
            ),
          ),
        ),
      ),
    ]));
  }
}
