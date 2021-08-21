// Import the test package and Counter class
import 'package:demo1/src/model/google_drive_link.dart';
import 'package:test/test.dart';
import 'package:http/http.dart' as http;

void main() {
  group('Shared folder checks', () {
    test('Extract folder id', () async {
      final fullUrl = 'https://drive.google.com/drive/folders/1iVioA824kgLlECPoa2x-XZsZ0fomeA5q';

      expect(GoogleDriveLink.getFolderId(fullUrl), '1iVioA824kgLlECPoa2x-XZsZ0fomeA5q');
    });

    test('Not shared folder', () async {
      final notSharedFolderId = '1iVioA824kgLlECPoa2x-XZsZ0fomeA5q';

      final folderLink =
          'http://drive.google.com/drive/folders/$notSharedFolderId';
      print(folderLink);
      final response = await http.get(Uri.parse(folderLink), headers: {
        'Accept': '*/*',
        'Access-Control-Allow-Origin': '*',
      });
      // print(
      //     'Response body ${response.body}, response status code is ${response.statusCode}');
      // ;
      expect(response.body.contains('"$notSharedFolderId"'), false);
    });

    test('Shared folder', () async {
      final sharedFolderId = '1vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n';

      final folderLink =
          'http://drive.google.com/drive/folders/$sharedFolderId';
      print(folderLink);
      final response = await http.get(Uri.parse(folderLink), headers: {
        'Accept': '*/*',
        'Access-Control-Allow-Origin': '*',
      });
      // print(
      //     'Response body ${response.body}, response status code is ${response.statusCode}');
      // ;
      expect(response.body.contains('"$sharedFolderId"'), true);
    });
  });
}
