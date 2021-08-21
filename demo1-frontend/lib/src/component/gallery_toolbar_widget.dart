import 'package:demo1/src/service/images_classifier_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'gallery_toolbar_widget/choose_images_source_button.dart';

const int SHARED_FOLDER_ID_MINIMAL_LENGTH = '1vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n'.length;

class GalleryToolbarWidget extends StatefulWidget {
  final ImagesClassifierService imagesClassifierService;

  GalleryToolbarWidget({Key? key, required this.imagesClassifierService})
      : super(key: key);

  @override
  _GalleryToolbarWidgetState createState() => _GalleryToolbarWidgetState();
}

class _GalleryToolbarWidgetState extends State<GalleryToolbarWidget> {
  late FocusNode _sharedFolderFocusNode;

  @override
  void initState() {
    super.initState();

    _sharedFolderFocusNode = FocusNode();
  }

  @override
  void dispose() {
    _sharedFolderFocusNode.dispose();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    var _columnsCountEditingController = TextEditingController(
        text: this.widget.imagesClassifierService.ColumnsCount?.toString());

    var _sharedFolderEditingController = TextEditingController(
        text: this.widget.imagesClassifierService.SharedFolder);

    return Container(
        alignment: Alignment.centerRight,
        child: Column(
          children: [
            Row(
              children: [
                Spacer(),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 4, 16, 0),
                  child: ChooseImagesSourceButton(
                      distance: 112.0,
                      child: SizedBox.fromSize(
                          size: Size(320, 50),
                          child: TextFormField(
                            focusNode: _sharedFolderFocusNode,
                            controller: _sharedFolderEditingController,
                            cursorColor: Color(0x0),
                            decoration: InputDecoration(
                              filled: true,
                              fillColor: Colors.white,
                              labelText:
                                  'Put path to the shared folder or folder id',
                              //errorText: widget._classesCount == 1 ? 'Value should be more then 2': '',
                              border: InputBorder.none,
                            ),
                            onChanged: (value) {
                              if (value.length >=
                                      SHARED_FOLDER_ID_MINIMAL_LENGTH) {
                                this.widget.imagesClassifierService.SharedFolder = value;
                              }
                            },
                          )),
                      childFocusNode: _sharedFolderFocusNode),
                ),
                Padding(
                  padding: EdgeInsets.fromLTRB(0, 0, 16, 0),
                  child: Container(
                      width: 120.0,
                      height: 50,
                      child: TextFormField(
                        controller: _columnsCountEditingController,
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
                          this.widget.imagesClassifierService.ColumnsCount =
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
