import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app_bar_title_widget/save_results_button.dart';

class ClassificationResultsTitleWidget extends StatefulWidget {
  final String title;
  final ImagesClassifierService imagesClassifierService;

  ClassificationResultsTitleWidget(
      {Key? key, required this.title, required this.imagesClassifierService})
      : super(key: key);

  @override
  _ClassificationResultsTitleWidgetState createState() =>
      _ClassificationResultsTitleWidgetState();
}

class _ClassificationResultsTitleWidgetState
    extends State<ClassificationResultsTitleWidget> {
  late FocusNode _classificationResultsFocusNode;

  @override
  void initState() {
    super.initState();

    _classificationResultsFocusNode = FocusNode();
  }

  @override
  void dispose() {
    _classificationResultsFocusNode.dispose();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    var _classesCountEditingController = TextEditingController(
        text: this.widget.imagesClassifierService.ClassesCount?.toString());
    var _titleEditingController =
        TextEditingController(text: this.widget.title);

    return Container(
        alignment: Alignment.centerRight,
        child: Column(
          children: [
            Row(
              children: [
                EditableText(
                    controller: _titleEditingController,
                    focusNode: _classificationResultsFocusNode,
                    style: const TextStyle(),
                    cursorColor: Colors.black,
                    backgroundCursorColor: Colors.green),
                Spacer(),
                Padding(
                    padding: EdgeInsets.fromLTRB(0, 6, 16, 0),
                    child: SaveResultsButton(
                      onPressed: () {
                        this
                            .widget
                            .imagesClassifierService
                            .FinishedClassification = true;
                      },
                    )),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 12, 0, 0),
                  child: Container(
                      width: 120.0,
                      height: 50,
                      child: TextFormField(
                        controller: _classesCountEditingController,
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
                          this.widget.imagesClassifierService.ClassesCount =
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
