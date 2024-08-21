package com.example.mhealth;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.hardware.Camera;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.TextureView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.io.DataOutputStream;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class DetectFragment extends Fragment implements View.OnClickListener {
    private String username;
    private TextView textView;
    private final int REQUEST_PICK_VIDEO = 1;
    private final int REQUEST_VIDEO_CAPTURE = 2;

    public DetectFragment() {
        // Required empty public constructor
    }

    public static DetectFragment newInstance(String username) {
        DetectFragment fragment = new DetectFragment();
        Bundle args = new Bundle();
        args.putString("USERNAME", username);
        fragment.setArguments(args);
        return fragment;
    }

    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            username = getArguments().getString("USERNAME");
        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_detect, container, false);

        // 初始化界面元素和设置点击监听器
        textView = view.findViewById(R.id.detect_textView);
        textView.setText("欢迎，" + username + "！\n请上传视频或拍摄视频以进行检测。\n注意：\n1. 请确保视频中仅包含您的面部。\n2. 请确保视频清晰，光线充足。\n3. 请不要佩戴眼镜等装饰物。\n4. 请确保视频时长不超过30s\n5. 您可以尝试用力闭眼、咧嘴以诱发相关症状。");

        Button startButton = view.findViewById(R.id.detect_button_detect);

        startButton.setOnClickListener(this);

        Button recordButton = view.findViewById(R.id.detect_button_record);

        recordButton.setOnClickListener(this);

        return view;
    }

    @Override
    public void onClick(View v) {
        if (v.getId() == R.id.detect_button_detect) {
            showChoiceDialog();
        } else if (v.getId() == R.id.detect_button_record) {
            Intent intent = new Intent(getActivity(), RecordActivity.class);
            startActivity(intent);
        }
    }

    private void showChoiceDialog() {
        requestPermissions();
        AlertDialog.Builder builder = new AlertDialog.Builder(getContext());
        builder.setTitle("选择视频源");
//        String[] options = {"上传本地视频", "拍摄视频"};
        String[] options = {"上传本地视频"};
        builder.setItems(options, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                if (which == 0) {
                    openVideoPicker();
                } else {
                    openCameraToRecordVideo();
                }
            }
        });
        AlertDialog dialog = builder.create();
        dialog.show();
    }

    private void openVideoPicker() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Video.Media.EXTERNAL_CONTENT_URI);
        startActivityForResult(intent, REQUEST_PICK_VIDEO);
    }

    private void openCameraToRecordVideo() {
        Intent intent = new Intent(MediaStore.ACTION_VIDEO_CAPTURE);
        intent.putExtra(MediaStore.EXTRA_DURATION_LIMIT, 60);
        intent.putExtra(MediaStore.EXTRA_VIDEO_QUALITY, 1);
        if (intent.resolveActivity(getActivity().getPackageManager()) != null) {
            startActivityForResult(intent, REQUEST_VIDEO_CAPTURE);
        }
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode == Activity.RESULT_OK) {
            String videoFilePath;
            if (requestCode == REQUEST_PICK_VIDEO) {
                Uri videoUri = data.getData();
                videoFilePath = getRealPathFromURI(getContext(), videoUri);
                uploadVideoWithParams(videoFilePath, username);
                Toast.makeText(getContext(), "视频上传中，请稍等", Toast.LENGTH_SHORT).show();
            } else if (requestCode == REQUEST_VIDEO_CAPTURE) {
                Uri videoUri = data.getData();
                videoFilePath = getRealPathFromURI(getContext(), videoUri);
                uploadVideoWithParams(videoFilePath, username);
                Toast.makeText(getContext(), "视频上传中，请稍等", Toast.LENGTH_SHORT).show();
            }
        }
    }

    public String getRealPathFromURI(Context context, Uri contentUri) {
        Cursor cursor = null;
        try {
            String[] proj = {MediaStore.Video.Media.DATA};
            cursor = context.getContentResolver().query(contentUri, proj, null, null, null);
            int column_index = cursor.getColumnIndexOrThrow(MediaStore.Video.Media.DATA);
            cursor.moveToFirst();
            return cursor.getString(column_index);
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }


    public void uploadVideoWithParams(String videoPath, String name) {
        OkHttpClient client = new OkHttpClient();
        File videoFile = new File(videoPath);

        Log.i("Upload", "Uploading video: " + videoFile.getName());
        long fileSize = videoFile.length();
        Log.i("Upload", "File size: " + fileSize);
        if (fileSize > 200 * 1024 * 1024) {
            Toast.makeText(getContext(), "视频文件过大，请重新选择", Toast.LENGTH_SHORT).show();
            return;
        }
        // 创建RequestBody，用于文件
        RequestBody videoBody = RequestBody.create(MediaType.parse("video/mp4"), videoFile);

        // 创建MultipartBody，添加视频和其他参数
        MultipartBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("video", videoFile.getName(), videoBody)
                .addFormDataPart("name", name)
                .build();

        // 创建Request对象
        Request request = new Request.Builder()
                .url("http://" + getString(R.string.ip_address) + "/api/detect/detect/")
                .post(requestBody)
                .build();

        // 异步请求
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                e.printStackTrace();
                Log.e("Upload", "Error uploading video", e);
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    Log.i("Upload", "Response: " + responseBody);
                } else {
                    Log.e("Upload", "Failed to upload video. Code: " + response.code());
                    Log.e("Upload", "Response: " + response.body().string());
                }
            }
        });
    }

    private static final int PERMISSION_REQUEST_CODE = 1;

    private void requestPermissions() {
        if (ContextCompat.checkSelfPermission(getActivity(), Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED
                || ContextCompat.checkSelfPermission(getActivity(), Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED
                || ContextCompat.checkSelfPermission(getActivity(), Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED
                || ContextCompat.checkSelfPermission(getActivity(), Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {

            ActivityCompat.requestPermissions(getActivity(),
                    new String[]{
                            Manifest.permission.CAMERA,
                            Manifest.permission.RECORD_AUDIO,
                            Manifest.permission.WRITE_EXTERNAL_STORAGE,
                            Manifest.permission.READ_EXTERNAL_STORAGE
                    },
                    PERMISSION_REQUEST_CODE);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                return;
            } else {
                // 权限请求被用户拒绝，向用户解释为什么需要这些权限
                Toast.makeText(getActivity(), "需要相机和录音权限", Toast.LENGTH_SHORT).show();
            }
        }
    }
}