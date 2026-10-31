package com.keiws.pensla;

import android.Manifest;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

// SPARA i appen: webbsidans nedladdning (a download) fungerar inte i
// appens WebView, så bilden skickas hit (PNG som base64) och sparas i
// Bilder/Pensla, där den syns i Galleri. Android 9 och äldre kräver
// lagringsbehörighet, som efterfrågas första gången.
@CapacitorPlugin(name = "Spara", permissions = @Permission(strings = { Manifest.permission.WRITE_EXTERNAL_STORAGE }, alias = "lagring"))
public class SparaPlugin extends Plugin {

    @PluginMethod
    public void bild(PluginCall call) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q && getPermissionState("lagring") != PermissionState.GRANTED) {
            requestPermissionForAlias("lagring", call, "efterBehorighet");
            return;
        }
        spara(call);
    }

    @PermissionCallback
    private void efterBehorighet(PluginCall call) {
        if (getPermissionState("lagring") == PermissionState.GRANTED) spara(call);
        else call.reject("Ingen behörighet att spara");
    }

    private void spara(PluginCall call) {
        String data = call.getString("data");
        String namn = call.getString("namn", "pensla.png");
        if (data == null) { call.reject("Ingen bild"); return; }
        try {
            byte[] png = Base64.decode(data, Base64.DEFAULT);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                ContentResolver cr = getContext().getContentResolver();
                ContentValues v = new ContentValues();
                v.put(MediaStore.Images.Media.DISPLAY_NAME, namn);
                v.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
                v.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/Pensla");
                Uri uri = cr.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
                if (uri == null) throw new Exception("Kunde inte skapa filen");
                try (OutputStream ut = cr.openOutputStream(uri)) { ut.write(png); }
            } else {
                File mapp = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "Pensla");
                mapp.mkdirs();
                File fil = new File(mapp, namn);
                try (FileOutputStream ut = new FileOutputStream(fil)) { ut.write(png); }
                android.media.MediaScannerConnection.scanFile(getContext(), new String[] { fil.getAbsolutePath() }, null, null);
            }
            call.resolve(new JSObject());
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }
}
