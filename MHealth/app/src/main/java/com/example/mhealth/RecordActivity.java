package com.example.mhealth;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.core.VideoCapture;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.ContentValues;
import android.content.pm.PackageManager;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.os.Handler;
import android.provider.MediaStore;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.google.common.util.concurrent.ListenableFuture;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executor;

public class RecordActivity extends AppCompatActivity implements View.OnClickListener {
    private ListenableFuture<ProcessCameraProvider> cameraProviderFuture;
    PreviewView previewView;
    Button bRecording;
    Button bSwitchCamera;
    private ImageCapture imageCapture;
    private VideoCapture videoCapture;
    private TextView countdownText;
    private TextView instructionText;
    private CountDownTimer countDownTimer;
    private MediaPlayer mediaPlayer;
    boolean isRecording = false;
    boolean useBackCamera = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_record);

        bRecording = findViewById(R.id.bRecord);
        bRecording.setText("开始录制");
        previewView = findViewById(R.id.previewView);

        countdownText = findViewById(R.id.countdownText);

        instructionText = findViewById(R.id.instructionText);

        bSwitchCamera = findViewById(R.id.bSwitchCamera);

        bRecording.setOnClickListener((View.OnClickListener) this);
        bSwitchCamera.setOnClickListener((View.OnClickListener) this);

        cameraProviderFuture = ProcessCameraProvider.getInstance(this);
        cameraProviderFuture.addListener(() -> {
            try {
                ProcessCameraProvider cameraProvider = cameraProviderFuture.get();
                startCameraX(cameraProvider, useBackCamera);
            } catch (Exception e) {
                Log.e("CameraX", "Use case binding failed", e);
            }

        }, getExecutor());

    }

    private Executor getExecutor() {
        return ContextCompat.getMainExecutor(this);
    }

    @SuppressLint("RestrictedApi")
    private void startCameraX(ProcessCameraProvider cameraProvider, boolean UseBackCamera) {

        cameraProvider.unbindAll();

        CameraSelector cameraSelector;
        if (UseBackCamera) {
            cameraSelector = new CameraSelector.Builder()
                    .requireLensFacing(CameraSelector.LENS_FACING_BACK)
                    .build();
        } else {
            cameraSelector = new CameraSelector.Builder()
                    .requireLensFacing(CameraSelector.LENS_FACING_FRONT)
                    .build();
        }

        Preview preview = new Preview.Builder().build();

        preview.setSurfaceProvider(previewView.getSurfaceProvider());

        imageCapture = new ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                .build();

        videoCapture = new VideoCapture.Builder()
                .setVideoFrameRate(60)
                .build();

        cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageCapture, videoCapture);
    }


    @SuppressLint("RestrictedApi")
    @Override
    public void onClick(View view) {
        if (view.getId() == R.id.bRecord) {
            if (bRecording.getText() == "开始录制") {
                startRecording();
                startCountdown();
            } else {
                stopRecording();
                stopCountdown();
            }
        }
        if (view.getId() == R.id.bSwitchCamera) {
            if (isRecording) {
                Toast.makeText(this, "请先停止录制", Toast.LENGTH_SHORT).show();
                return;
            }
            useBackCamera = !useBackCamera;
            cameraProviderFuture.addListener(() -> {
                try {
                    ProcessCameraProvider cameraProvider = cameraProviderFuture.get();
                    startCameraX(cameraProvider, useBackCamera);
                } catch (ExecutionException | InterruptedException e) {
                    e.printStackTrace();
                }
            }, getExecutor());
        }
    }

    @SuppressLint("RestrictedApi")
    private void recordVideo() {
        if (videoCapture != null) {
            long timeStamp = System.currentTimeMillis();
            ContentValues contentValues = new ContentValues();
            contentValues.put(MediaStore.MediaColumns.DISPLAY_NAME, timeStamp);
            contentValues.put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4");


            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                // TODO: Consider calling
                //    ActivityCompat#requestPermissions
                // here to request the missing permissions, and then overriding
                //   public void onRequestPermissionsResult(int requestCode, String[] permissions,
                //                                          int[] grantResults)
                // to handle the case where the user grants the permission. See the documentation
                // for ActivityCompat#requestPermissions for more details.
                return;
            }
            videoCapture.startRecording(
                    new VideoCapture.OutputFileOptions.Builder(
                            getContentResolver(),
                            MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
                            contentValues
                    ).build(),
                    getExecutor(),
                    new VideoCapture.OnVideoSavedCallback() {
                        @Override
                        public void onVideoSaved(@NonNull VideoCapture.OutputFileResults outputFileResults) {
                            Toast.makeText(RecordActivity.this, "Saving...", Toast.LENGTH_SHORT).show();
                        }

                        @Override
                        public void onError(int videoCaptureError, @NonNull String message, @Nullable Throwable cause) {
                            Toast.makeText(RecordActivity.this, "Error: " + message, Toast.LENGTH_SHORT).show();
                        }
                    }

            );
        }
    }

    @SuppressLint("RestrictedApi")
    private void startRecording() {
        isRecording = true;
        bRecording.setText("停止录制");
        recordVideo();
    }

    @SuppressLint("RestrictedApi")
    private void stopRecording() {
        isRecording = false;
        bRecording.setText("开始录制");
        videoCapture.stopRecording();
        instructionText.setText("请点击上方按钮开始录制");
    }

    @SuppressLint("RestrictedApi")
    private void startCountdown() {
        countDownTimer = new CountDownTimer(50000, 1000) {
            public void onTick(long millisUntilFinished) {
                countdownText.setText(String.valueOf(millisUntilFinished / 1000));
                int seconds = (int) (millisUntilFinished / 1000);
                if (seconds > 0 && seconds < 10) {
                    instructionText.setText("请注视摄像头，保持不动");
                } else if (seconds >= 10 && seconds < 20) {
                    instructionText.setText("请用力咧嘴，重复2次");
                } else if (seconds >= 20 && seconds < 30) {
                    instructionText.setText("请注视摄像头，保持不动");
                } else if (seconds >= 30 && seconds < 40) {
                    instructionText.setText("请用力闭眼，重复3次");
                } else if (seconds >= 40 && seconds < 50) {
                    instructionText.setText("请注视摄像头，保持不动");
                } else {
                    instructionText.setText("请注视摄像头，保持不动");
                }

                if (seconds == 9 || seconds == 29 || seconds == 49) {
                    playSound(1);
                } else if (seconds == 19) {
                    playSound(2);
                } else if (seconds == 39) {
                    playSound(3);
                }
            }

            public void onFinish() {
                countdownText.setText("0");
                stopRecording();
            }
        }.start();
    }

    private void playSound(int soundId) {
        if (mediaPlayer != null) {
            mediaPlayer.stop();
            mediaPlayer.release(); // 释放当前 MediaPlayer 资源
        }

        if (soundId == 1) {
            mediaPlayer = MediaPlayer.create(this, R.raw.staystable);
        } else if (soundId == 2) {
            mediaPlayer = MediaPlayer.create(this, R.raw.openmouth);
        } else if (soundId == 3) {
            mediaPlayer = MediaPlayer.create(this, R.raw.closeeye);
        }

        mediaPlayer.start();
    }

    @SuppressLint("RestrictedApi")
    private void stopCountdown() {
        if (countDownTimer != null) {
            countDownTimer.cancel();
            countdownText.setText("0");
            stopRecording();
        }
    }
}