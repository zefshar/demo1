import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppBarTitleWidget extends StatelessWidget {
  final String title;
  final ImagesClassifierService imagesClassifierService;

  AppBarTitleWidget(
      {Key? key, required this.title, required this.imagesClassifierService})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    var _textEditingController = TextEditingController(text: this.imagesClassifierService.ClassesCount?.toString());
    return Container(
        alignment: Alignment.centerRight,
        child: Column(
          children: [
            Row(
              children: [
                Text(this.title),
                Spacer(),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 8, 16, 0),
                  child: IconButton(onPressed: () {}, icon: const Icon(Icons.download_rounded),)
                ),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 12, 0, 0),
                  child: Container(
                      width: 120.0,
                      height: 50,
                      child: TextFormField(
                        controller: _textEditingController,
                        cursorColor: Color(0x0),
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: Colors.white,
                          labelText: 'Classes count',
                          //errorText: widget._classesCount == 1 ? 'Value should be more then 2': '',
                          border: InputBorder.none,
                        ),
                        keyboardType: TextInputType.number,
                        onChanged: (value) {
                          this.imagesClassifierService.ClassesCount =
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

