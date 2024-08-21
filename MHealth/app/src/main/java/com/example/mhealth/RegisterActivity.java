package com.example.mhealth;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;

public class RegisterActivity extends AppCompatActivity {
    enum RegisterStatus {
        SUCCESS,
        EMPTY_FIELD,
        PASSWORD_MISMATCH,
        USER_EXISTS,
        INVALID_USERNAME,
        UNKNOWN_ERROR
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        Button registerButton = findViewById(R.id.register_button_register);
        registerButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                EditText usernameEditText = findViewById(R.id.register_username);
                EditText passwordEditText = findViewById(R.id.register_password);
                EditText confirmPasswordEditText = findViewById(R.id.register_confirm_password);
                String username = usernameEditText.getText().toString();
                String password = passwordEditText.getText().toString();
                String confirmPassword = confirmPasswordEditText.getText().toString();
                isValid(username, password, confirmPassword, new ApiResponseListener() {
                    @Override
                    public void registerResponse(RegisterStatus registerStatus) {
                        if (registerStatus == RegisterStatus.SUCCESS) {
                            runOnUiThread(new Runnable() {
                                @Override
                                public void run() {
                                    Toast.makeText(RegisterActivity.this, "Register success", Toast.LENGTH_SHORT).show();
                                }
                            });
                            Intent intent = new Intent(RegisterActivity.this, MainActivity.class);
                            startActivity(intent);
                        } else {
                            String error_msg = "";
                            // 注册失败，显示错误消息
                            if (registerStatus == RegisterStatus.EMPTY_FIELD) {
                                error_msg = "Please fill in all fields";
                            } else if (registerStatus == RegisterStatus.PASSWORD_MISMATCH) {
                                error_msg = "Passwords do not match";
                            } else if (registerStatus == RegisterStatus.USER_EXISTS) {
                                error_msg = "User already exists";
                            } else if (registerStatus == RegisterStatus.INVALID_USERNAME) {
                                error_msg = "Username can only contain letters and numbers";
                            } else {
                                error_msg = "Unknown error";
                            }
                            String finalError_msg = error_msg;
                            runOnUiThread(new Runnable() {
                                @Override
                                public void run() {
                                    Toast.makeText(RegisterActivity.this, finalError_msg, Toast.LENGTH_SHORT).show();
                                }
                            });
                        }
                    }
                });
            }
        });

        Button backToLoginButton = findViewById(R.id.register_button_back);
        backToLoginButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent intent = new Intent(RegisterActivity.this, MainActivity.class);
                startActivity(intent);
            }
        });
    }

    public interface ApiResponseListener {
        void registerResponse(RegisterStatus registerStatus);
    }

    public boolean isValidString(String str) {
        // 定义用户名只能包含大小写字母和数字的正则表达式
        String regex = "^[a-zA-Z0-9]+$";

        // 使用正则表达式验证用户名
        return str.matches(regex);
    }

    public void isValid(String username, String password, String confirmPassword, ApiResponseListener listener) {
        if (username.isEmpty() || password.isEmpty() || confirmPassword.isEmpty()) {
            listener.registerResponse(RegisterStatus.EMPTY_FIELD);
            return;
        }
        if (!isValidString(username)) {
            listener.registerResponse(RegisterStatus.INVALID_USERNAME);
            return;
        }
        if (!isValidString(password) || !isValidString(confirmPassword)) {
            listener.registerResponse(RegisterStatus.INVALID_USERNAME);
            return;
        }
        if (!password.equals(confirmPassword)) {
            listener.registerResponse(RegisterStatus.PASSWORD_MISMATCH);
            return;
        }
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // 创建URL对象
                    URL url = new URL("http://" + getResources().getText(R.string.ip_address) + "/api/user/register/");

                    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                    connection.setRequestMethod("POST");
//                    connection.setRequestProperty("Content-Type", "application/json");
                    connection.setDoOutput(true);

                    Log.d("Register", "Request: " + username + " " + password);

                    // 设置请求体参数
                    String params = "name=" + URLEncoder.encode(username, "UTF-8") + "&password=" + URLEncoder.encode(password, "UTF-8");
                    connection.setDoOutput(true);
                    OutputStream outputStream = connection.getOutputStream();
                    outputStream.write(params.getBytes());
                    outputStream.flush();
                    outputStream.close();

                    // 获取服务器响应状态码
                    int responseCode = connection.getResponseCode();
                    Log.d("Register", "Response code: " + responseCode);

                    if (responseCode != 200) {
                        Log.d("Login", connection.getInputStream().toString());
                        listener.registerResponse(RegisterStatus.UNKNOWN_ERROR);
                    }

                    // 读取服务器响应内容
                    BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        response.append(line);
                    }
                    reader.close();

                    // 在这里解析并验证服务器返回的结果，根据返回结果进行相应的处理
                    String responseBody = response.toString();
                    Log.d("Register", responseBody);
                    // 这里假设返回结果是JSON格式的数据，你可以根据实际情况进行解析
                    JSONObject jsonResponse = new JSONObject(responseBody);
                    int code = jsonResponse.getInt("code");
                    // 将响应状态码传递给回调接口
                    if (code == 200) {
                        listener.registerResponse(RegisterStatus.SUCCESS);
                    } else if (code == 400) {
                        listener.registerResponse(RegisterStatus.USER_EXISTS);
                    } else {
                        listener.registerResponse(RegisterStatus.UNKNOWN_ERROR);
                    }
                } catch (Exception e) {
                    Log.d("Login Error", e.toString());
                    listener.registerResponse(RegisterStatus.UNKNOWN_ERROR);
                }
            }
        }).start();
    }

}