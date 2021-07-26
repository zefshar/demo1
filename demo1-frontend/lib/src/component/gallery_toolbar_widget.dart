import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class GalleryToolbarWidget extends StatelessWidget {
  final ImagesClassifierService imagesClassifierService;

  GalleryToolbarWidget(
      {Key? key, required this.imagesClassifierService})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    var _textEditingController = TextEditingController(text: this.imagesClassifierService.ColumnsCount?.toString());
    return Container(
        alignment: Alignment.centerRight,
        child: Column(
          children: [
            Row(
              children: [
                Spacer(),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 4, 16, 0),
                  child: IconButton(onPressed: () {}, icon: const Icon(Icons.upload_rounded))
                ),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 0, 16, 0),
                  child: Container(
                      width: 120.0,
                      height: 50,
                      child: TextFormField(
                        controller: _textEditingController,
                        cursorColor: Color(0x0),
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: Colors.white,
                          labelText: 'Columns count',
                          //errorText: widget._classesCount == 1 ? 'Value should be more then 2': '',
                          border: InputBorder.none,
                        ),
                        keyboardType: TextInputType.number,
                        onChanged: (value) {
                          this.imagesClassifierService.ColumnsCount =
                              value.isEmpty ? null : int.parse(value);
                        },
                        inputFormatters: <TextInputFormatter>[
                          FilteringTextInputFormatter.digitsOnly
                        ], // Only numbers can be entered
                      )),
                )
              ],
            )
          ],
        ));
  }
}

