import 'package:flutter/material.dart';

/// Image representation
class ImageCardWidget extends StatelessWidget {
  final int index;

  const ImageCardWidget({required this.index, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Card(
        child: Column(
          mainAxisSize: MainAxisSize.max,
          children: <Widget>[
            // const ListTile(
            //   leading: Icon(Icons.album),
            //   title: Text('The Enchanted Nightingale'),
            //   subtitle: Text('Music by Julie Gable. Lyrics by Sidney Stein.'),
            // ),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: <Widget>[
                TextButton(
                  child: const Text('BUY TICKETS'),
                  onPressed: () {/* ... */},
                ),
                const SizedBox(width: 8),
                TextButton(
                  child: const Text('LISTEN'),
                  onPressed: () {/* ... */},
                ),
                const SizedBox(width: 8),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
