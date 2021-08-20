extension IterableX<T> on Iterable<T> {
  /// The last index on this iterable.
  ///
  /// Ie `[A,B,C].lastIndex == 2`
  int get lastIndex => length == 0
      ? throw RangeError('Cannot find the last index of an empty iterable')
      : length - 1;
}