// Hooks de observacion para Frida: red, criptografia, carga de codigo y shell.
// Solo registra eventos (no altera el comportamiento de la aplicacion).
// Uso: python3 scripts/frida/run_hooks.py <paquete> scripts/frida/hooks.js <salida>

Java.perform(function () {
    send('[*] hooks instalados en ' + Java.use('android.os.Process').myPid());

    // URLs construidas con java.net.URL
    try {
        var URL = Java.use('java.net.URL');
        URL.$init.overload('java.lang.String').implementation = function (u) {
            send('[URL] ' + u);
            return this.$init(u);
        };
    } catch (e) { send('[!] URL: ' + e); }

    // HttpURLConnection / HttpsURLConnection
    try {
        var HttpsConn = Java.use('javax.net.ssl.HttpsURLConnection');
        HttpsConn.connect.implementation = function () {
            send('[HttpsURLConnection] ' + this.getURL());
            return this.connect();
        };
    } catch (e) { send('[!] HttpsURLConnection: ' + e); }

    // OkHttp (por si alguna dependencia lo usa)
    try {
        var OkReq = Java.use('okhttp3.Request$Builder');
        OkReq.build.implementation = function () {
            var r = this.build();
            try { send('[OkHttp] ' + r.url().toString()); } catch (e2) {}
            return r;
        };
    } catch (e) { /* okhttp no presente: normal en apps Flutter */ }

    // Criptografia: algoritmos usados y tamano de datos
    try {
        var Cipher = Java.use('javax.crypto.Cipher');
        Cipher.doFinal.overload('[B').implementation = function (input) {
            send('[Cipher.doFinal] alg=' + this.getAlgorithm() + ' tam=' + (input ? input.length : 0));
            return this.doFinal(input);
        };
    } catch (e) { send('[!] Cipher: ' + e); }

    // Carga dinamica de codigo
    try {
        var DCL = Java.use('dalvik.system.DexClassLoader');
        DCL.$init.implementation = function (dexPath, opt, libPath, parent) {
            send('[DexClassLoader] ' + dexPath);
            return this.$init(dexPath, opt, libPath, parent);
        };
    } catch (e) { /* sin uso */ }

    // Ejecucion de comandos
    try {
        var RT = Java.use('java.lang.Runtime');
        RT.exec.overload('java.lang.String').implementation = function (cmd) {
            send('[Runtime.exec] ' + cmd);
            return this.exec(cmd);
        };
    } catch (e) { /* sin uso */ }

    // Librerias nativas cargadas
    try {
        var Sys = Java.use('java.lang.System');
        Sys.loadLibrary.implementation = function (lib) {
            send('[System.loadLibrary] ' + lib);
            return this.loadLibrary(lib);
        };
    } catch (e) { send('[!] loadLibrary: ' + e); }

    // TrustManagers personalizados (indicador de pinning)
    try {
        var SSLctx = Java.use('javax.net.ssl.SSLContext');
        SSLctx.init.overload('[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation = function (km, tm, sr) {
            if (tm && tm.length > 0) {
                send('[SSLContext.init] TrustManager: ' + tm[0].getClass().getName());
            }
            return this.init(km, tm, sr);
        };
    } catch (e) { /* sin uso */ }

    // Instalacion de paquetes (REQUEST_INSTALL_PACKAGES)
    try {
        var PM = Java.use('android.app.ApplicationPackageManager');
        PM.getPackageInfo.overload('java.lang.String', 'int').implementation = function (p, f) {
            send('[getPackageInfo] ' + p + ' flags=' + f);
            return this.getPackageInfo(p, f);
        };
    } catch (e) { /* sin uso */ }
});
