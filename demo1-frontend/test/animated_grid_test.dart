import 'package:demo1/src/component/animated_grid/animated_grid.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  group('AnimatedGrid', () {
    test('gridIndicies', () {
      /// index 0
      ///
      /// ```
      /// 0 2
      /// 1
      /// ```
      expect(
        AnimatedGrid.gridIndicies(0, 2, 3),
        equals([0, 0]),
      );

      /// index 2
      ///
      /// ```
      /// 0 2
      /// 1
      /// ```
      expect(
        AnimatedGrid.gridIndicies(2, 2, 3),
        equals([1, 0]),
      );

      /// index 9
      ///
      /// ```
      /// 0 4 8
      /// 1 5 9
      /// 2 6
      /// 3 7
      /// ```
      expect(
        AnimatedGrid.gridIndicies(9, 3, 10),
        equals([2, 1]),
      );

      /// index 7
      ///
      /// ```
      /// 0 4 8
      /// 1 5 9
      /// 2 6
      /// 3 7
      /// ```
      expect(
        AnimatedGrid.gridIndicies(7, 3, 10),
        equals([1, 3]),
      );

      /// index 6
      ///
      /// ```
      /// 0 4 8
      /// 1 5 9
      /// 2 6
      /// 3 7
      /// ```
      expect(
        AnimatedGrid.gridIndicies(6, 3, 10),
        equals([1, 2]),
      );

      /// index 3
      ///
      /// ```
      /// 0 4 8
      /// 1 5 9
      /// 2 6
      /// 3 7
      /// ```
      expect(
        AnimatedGrid.gridIndicies(3, 3, 10),
        equals([0, 3]),
      );
    });
  });
}