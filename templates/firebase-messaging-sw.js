importScripts('https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.0/firebase-messaging.js');

firebase.initializeApp({
  'apiKey': "AIzaSyD82XzcT6tZCWL8-hVyBXLYfazYG9q1BJQ",
  'authDomain': "ipdc-mts-dms.firebaseapp.com",
  'projectId': "ipdc-mts-dms",
  'storageBucket': "ipdc-mts-dms.appspot.com",
  'messagingSenderId': "1051048974784",
  'appId': "1:1051048974784:web:a6e530a4c24ee2f5c1d025"
});

const messaging = firebase.messaging();

messaging.setBackgroundMessageHandler(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);

  payload = payload.data;
  const notificationTitle = payload.title;
  const notificationOptions = {
    body: payload.body,
    icon: payload.icon_url,
  };

  self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    clients.openWindow(payload.url);
  });

  return self.registration.showNotification(notificationTitle,
      notificationOptions);
});