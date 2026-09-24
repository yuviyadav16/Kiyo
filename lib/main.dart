import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:async';
import 'dart:convert';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PrivateInstagramApp());
}

class PrivateInstagramApp extends StatelessWidget {
  const PrivateInstagramApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Private IG',
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.black, 
      ),
      home: const SplashScreen(),
    );
  }
}

// --- NATIVE SPLASH SCREEN ---
class SplashScreen extends StatefulWidget {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // 2 second baad Instagram khulega
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
          width: 90,
          height: 90,
        ),
      ),
    );
  }
}

// --- THE HIDDEN ENGINE (WebView & JS Injection) ---
class IGWebViewScreen extends StatefulWidget {
  const IGWebViewScreen({Key? key}) : super(key: key);

  @override
  State<IGWebViewScreen> createState() => _IGWebViewScreenState();
}

class _IGWebViewScreenState extends State<IGWebViewScreen> {
  InAppWebViewController? webViewController;
  
  // Vercel Backend URL
  final String backendUrl = "https://kiyo-one.vercel.app/api/check_rule";

  InAppWebViewSettings settings = InAppWebViewSettings(
    javaScriptEnabled: true,
    transparentBackground: true,
    disableHorizontalScroll: true,
    supportZoom: false,
    builtInZoomControls: false,
    displayZoomControls: false,
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: InAppWebView(
          initialUrlRequest: URLRequest(url: WebUri("https://www.instagram.com/")),
          initialSettings: settings,
          onWebViewCreated: (controller) {
            webViewController = controller;

            // --- JAVASCRIPT SE FLUTTER MEIN DATA LAANE KA BRIDGE ---
            // Jab koi Fake Post share karega, toh JS ye function call karegi
            controller.addJavaScriptHandler(
              handlerName: 'saveLocalPost',
              callback: (args) async {
                // args mein [photoBase64, caption] aayega
                if (args.isNotEmpty) {
                  String photoData = args[0]['photo'];
                  String caption = args[0]['caption'];
                  
                  // Local memory mein save karo
                  SharedPreferences prefs = await SharedPreferences.getInstance();
                  List<String> savedPosts = prefs.getStringList('my_fake_posts') ?? [];
                  
                  var newPost = {"photo": photoData, "caption": caption, "time": DateTime.now().toString()};
                  savedPosts.add(jsonEncode(newPost));
                  await prefs.setStringList('my_fake_posts', savedPosts);
                  
                  print("Local Post Saved Successfully! Data hidden from IG Servers.");
                }
              },
            );
          },
          
          // JAISE HI PAGE LOAD HOGA, HUMARI HACKER SCRIPT INJECT HOGI
          onLoadStop: (controller, url) async {
            String jsCode = """
              // 1. Account Settings/Privacy button ko completely hide karna
              function hideSettings() {
                // IG ke classes change hote rehte hain, DOM inspect karke exact class dalna padega
                let privacyBtn = document.querySelector('a[href="/accounts/privacy_and_security/"]');
                if(privacyBtn) privacyBtn.style.setProperty('display', 'none', 'important');
              }
              
              // 2. Story ka Green Ring Pink (Normal) mein badalna
              function hideCloseFriendsRing() {
                let greenRings = document.querySelectorAll('svg circle[stroke="#1ED760"]'); // IG ka green color code
                greenRings.forEach(ring => {
                  ring.setAttribute('stroke', '#d62976'); // Asli pinkish-orange IG gradient color daal do
                });
                
                let greenStar = document.querySelector('svg[aria-label="Close Friends"]');
                if(greenStar) greenStar.style.display = 'none';
              }

              // 3. Fake Post Upload Intercept (Server pe upload block karke Flutter ko bhejna)
              function interceptPostShare() {
                let shareBtn = document.querySelector('div[role="button"]:contains("Share")'); 
                if(shareBtn) {
                  shareBtn.addEventListener('click', function(e) {
                    e.preventDefault(); // Upload cancel!
                    e.stopPropagation();
                    
                    // Canvas ya img tag se image ka Base64 data nikalna
                    let imgElement = document.querySelector('img[alt="Image to be shared"]');
                    let captionBox = document.querySelector('div[aria-label="Write a caption..."]');
                    
                    let photoData = imgElement ? imgElement.src : '';
                    let captionTxt = captionBox ? captionBox.innerText : '';
                    
                    // Flutter ko signal bhejo ki save kar le
                    window.flutter_inappwebview.callHandler('saveLocalPost', {
                      'photo': photoData, 
                      'caption': captionTxt
                    });
                    
                    // User ko lagega post ho gaya (UI reset kar do)
                    alert('Posted successfully!'); // Iski jagah custom native toast laga sakte ho
                    window.location.href = "/"; // Home pe bhej do
                  }, true);
                }
              }

              // Script ko continuously chalate raho kyunki IG single-page app (React) hai
              setInterval(() => {
                hideSettings();
                hideCloseFriendsRing();
                interceptPostShare();
              }, 1000);
            """;
            
            await controller.evaluateJavascript(source: jsCode);
          },
        ),
      ),
    );
  }
}
