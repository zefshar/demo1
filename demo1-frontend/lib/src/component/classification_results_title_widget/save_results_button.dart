import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';

@immutable
class SaveResultsButton extends StatefulWidget {
  const SaveResultsButton({
    Key? key,
    this.initialOpen,
    this.onPressed,
  }) : super(key: key);

  final bool? initialOpen;
  final VoidCallback? onPressed;

  @override
  _SaveResultsButtonState createState() => _SaveResultsButtonState();
}

class _SaveResultsButtonState extends State<SaveResultsButton>
    with SingleTickerProviderStateMixin {
  bool _open = false;

  @override
  void initState() {
    super.initState();
    _open = widget.initialOpen ?? false;
  }

  void _toggle() {
    setState(() {
      _open = !_open;
      if (_open && widget.onPressed != null) {
        widget.onPressed!();
        WidgetsBinding.instance?.addPostFrameCallback((_) {
          setState(() {
            _open = false;
          });
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      child: Stack(
        alignment: Alignment.bottomRight,
        clipBehavior: Clip.none,
        children: [
          _buildTapToCloseFab(),
          _buildTapToOpenFab(),
        ],
      ),
    );
  }

  Widget _buildTapToCloseFab() {
    return SizedBox(
      width: 56.0,
      height: 56.0,
      child: Center(
        child: Material(
          shape: const CircleBorder(),
          clipBehavior: Clip.antiAlias,
          elevation: 4.0,
          child: InkWell(
            onTap: _toggle,
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: Icon(
                Icons.close,
                color: Theme.of(this.context).primaryColor,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTapToOpenFab() {
    return IgnorePointer(
      ignoring: _open,
      child: AnimatedContainer(
        transformAlignment: Alignment.center,
        transform: Matrix4.diagonal3Values(
          _open ? 0.7 : 1.0,
          _open ? 0.7 : 1.0,
          1.0,
        ),
        duration: const Duration(milliseconds: 250),
        curve: const Interval(0.0, 0.5, curve: Curves.easeOut),
        child: AnimatedOpacity(
          opacity: _open ? 0.0 : 1.0,
          curve: const Interval(0.25, 1.0, curve: Curves.easeInOut),
          duration: const Duration(milliseconds: 250),
          child: FloatingActionButton(
            elevation: 0,
            backgroundColor: Theme.of(this.context).primaryColor,
            hoverElevation: 0,
            onPressed: _toggle,
            child: const Icon(Icons.download),
          ),
        ),
      ),
    );
  }

}
