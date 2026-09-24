import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'dart:async';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyPrivateApp());
}

class MyPrivateApp extends StatelessWidget {
  const MyPrivateApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Private IG',
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.black, // IG ki dark theme se match karne ke liye
      ),
      home: const SplashScreen(),
    );
  }
}

// --- SPLASH SCREEN (Native look ke liye) ---
class SplashScreen extends StatefulWidget {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // 2 second baad automatically WebView par chala jayega
    Timer(const Duration(seconds: 2), () {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const IGWebViewScreen()),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Image.asset(
          'assets/2308.png',
          width: 80, // Logo ka size apne hisaab se adjust kar lena
          height: 80,
        ),
      ),
    );
  }
}

// --- HIDDEN WEBVIEW SCREEN ---
class IGWebViewScreen extends StatefulWidget {
  const IGWebViewScreen({Key? key}) : super(key: key);

  @override
  State<IGWebViewScreen> createState() => _IGWebViewScreenState();
}

class _IGWebViewScreenState extends State<IGWebViewScreen> {
  InAppWebViewController? webViewController;

  // WebView ki settings jisse wo website na lagkar App lage
  InAppWebViewSettings settings = InAppWebViewSettings(
    javaScriptEnabled: true,
    transparentBackground: true,
    disableHorizontalScroll: true,
    disableVerticalScroll: false,
    supportZoom: false, // Zoom disable kar diya taki website jaisa feel na ho
    builtInZoomControls: false,
    displayZoomControls: false,
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // SafeArea hatane se screen ekdum top edge tak jayegi (Immersive Native feel)
      body: InAppWebView(
        initialUrlRequest: URLRequest(url: WebUri("https://www.instagram.com/")),
        initialSettings: settings,
        onWebViewCreated: (controller) {
          webViewController = controller;
        },
        onLoadStop: (controller, url) async {
          // Yahan hum baad mein apni JAVASCRIPT INJECT karenge
          // jo comments fake karegi aur backend verify karegi
          print("Page Loaded: $url");
        },
      ),
    );
  }
}
