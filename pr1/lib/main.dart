import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter/foundation.dart';

void main() {
  runApp(PrOneApp());
}

class PrOneApp extends StatelessWidget {
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      routes: {'/': (context) => PrOneScreen()},
    );
  }
}

class PrOneScreen extends StatelessWidget {
  static const int _pr1ColorPrimaryValue = 0xFFD7BBFA;
  static const int _pr1ColorPrimaryValue500 = 0xFF712FCE;
  static const int _pr1ColorPrimaryValue600 = 0xFF5F2DC7;
  static const int _pr1ColorPrimaryValue700 = 0xFF442ABE;
  static const int _pr1ColorPrimaryValue800 = 0xFF2427B5;
  static const int _pr1ColorSecondaryValue = 0xFFDEFABB;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(_pr1ColorSecondaryValue),
      body: Center(
        child: SizedBox(
          width: 400,
          child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                SvgPicture.asset(
                  kIsWeb ? 'images/logo1.svg': 'assets/images/logo1.svg',
                  width: 400,
                  height: 400,
                  color: Color(_pr1ColorPrimaryValue500),
                ),
                Text(
                  'Done is beautiful',
                  style: TextStyle(
                      color: Color(_pr1ColorPrimaryValue),
                      fontSize: 45,
                      fontWeight: FontWeight.w600),
                ),
                Align(
                  alignment: Alignment.bottomRight,
                  child: Text(
                    'Sergey Loskutov Group',
                    style: TextStyle(
                        color: Color(_pr1ColorPrimaryValue500),
                        fontStyle: FontStyle.italic,
                        fontSize: 10,
                        fontWeight: FontWeight.w400),
                  ),
                )
              ]),
        ),
      ),
    );
  }
}
