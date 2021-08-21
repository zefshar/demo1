
class GoogleDriveLink  {

  static const String FOLDER_REGEXP_D1 = r'([\w-]{33}|[\w-]{19})';

  static String getFolderId(String fullUrl) {
    final matchResult = RegExp(FOLDER_REGEXP_D1).firstMatch(fullUrl);
    return matchResult != null ? matchResult[0]!: '';
  }

}