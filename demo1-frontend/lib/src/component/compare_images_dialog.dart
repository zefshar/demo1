import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';

class CompareImagesDialog extends StatelessWidget {
  final String? oldImageUrl;
  final String? newImageUrl;

  CompareImagesDialog(this.oldImageUrl, this.newImageUrl);

  @override
  Widget build(BuildContext context) {
    return Dialog(
        child: Row(
      children: [
        Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
              image: DecorationImage(
                  image: NetworkImage(this.oldImageUrl ??
                      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='),
                  fit: BoxFit.cover)),
        ),
        Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
              image: DecorationImage(
                  image: NetworkImage(this.newImageUrl ??
                      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='),
                  fit: BoxFit.cover)),
        ),
      ],
    ));
  }
}
