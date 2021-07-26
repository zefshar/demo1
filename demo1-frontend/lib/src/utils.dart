String GetExcelColumnName(int columnNumber) {
  int dividend = columnNumber;
  String columnName = '';
  int modulo;

  while (dividend > 0) {
    modulo = (dividend - 1) % 26;
    columnName = String.fromCharCode(65 + modulo) + columnName;
    dividend = ((dividend - modulo) / 26).round();
  }

  return columnName;
}
