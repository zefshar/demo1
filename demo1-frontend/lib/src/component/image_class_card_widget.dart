import 'package:demo1/src/utils.dart';
import 'package:flutter/material.dart';

/// Image class representation
class ImageClassCardWidget extends StatelessWidget {
  final int index;
  final int count = 0;

  const ImageClassCardWidget({required this.index, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Card(
        child: Column(
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
                    '${GetExcelColumnName(index + 1)}',
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
                      image: NetworkImage(
                          'https://flutter.github.io/assets-for-api-docs/assets/widgets/owl.jpg'),
                    ))),
          ],
        ),
      ),
    );
  }
}
