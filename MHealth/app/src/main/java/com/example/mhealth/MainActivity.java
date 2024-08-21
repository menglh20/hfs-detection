package com.example.mhealth;

import android.content.Intent;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

import android.text.TextUtils;
import android.util.Log;
import android.view.View;

import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;


public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loginButton = findViewById(R.id.login_button_login);
        loginButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 获取用户名和密码
                EditText usernameEditText = findViewById(R.id.login_username);
                EditText passwordEditText = findViewById(R.id.login_password);
                String username = usernameEditText.getText().toString();
                String password = passwordEditText.getText().toString();
                isValid(username, password, new ApiResponseListener() {
                    @Override
                    public void loginResponse(boolean isSuccessful) {

                        ///////
                        isSuccessful = true; // 绕过登陆
                        ///////

                        if (isSuccessful) {
                            // 登录成功，跳转到下一个Activity
                            Intent intent = new Intent(MainActivity.this, HomeActivity.class);
                            // 将用户名作为额外数据放入 Intent
                            intent.putExtra("USERNAME", username);
                            startActivity(intent);
                        } else {
                            // 登录失败，显示错误消息
                            runOnUiThread(new Runnable() {
                                @Override
                                public void run() {
                                    Toast.makeText(MainActivity.this, "Invalid username or password", Toast.LENGTH_SHORT).show();
                                }
                            });
                        }
                    }
                });
            }
        });

        Button registerButton = findViewById(R.id.login_button_register);
        registerButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(MainActivity.this, RegisterActivity.class);
                startActivity(intent);
            }
        });
    }

    public interface ApiResponseListener {
        void loginResponse(boolean isSuccessful);
    }

    // 验证用户名和密码的方法
    private void isValid(String username, String password, ApiResponseListener listener) {
        if (TextUtils.isEmpty(username) || TextUtils.isEmpty(password)) {
            listener.loginResponse(false);
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // 创建URL对象
                    URL url = new URL("http://" + getResources().getText(R.string.ip_address) + "/api/user/login/");

                    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                    connection.setRequestMethod("POST");
                    connection.setDoOutput(true);

                    Log.d("Login", "Request: " + username + " " + password);

                    // 设置请求体参数
                    String params = "name=" + URLEncoder.encode(username, "UTF-8") + "&password=" + URLEncoder.encode(password, "UTF-8");
                    connection.setDoOutput(true);
                    OutputStream outputStream = connection.getOutputStream();
                    outputStream.write(params.getBytes());
                    outputStream.flush();
                    outputStream.close();

                    // 获取服务器响应状态码
                    int responseCode = connection.getResponseCode();
                    Log.d("Login", "Response code: " + responseCode);

                    if (responseCode != 200) {
                        Log.d("Login", connection.getInputStream().toString());
                        listener.loginResponse(false);
                        return;
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
                    Log.d("Login", responseBody);
                    // 这里假设返回结果是JSON格式的数据，你可以根据实际情况进行解析
                    JSONObject jsonResponse = new JSONObject(responseBody);
                    int code = jsonResponse.getInt("code");
                    // 将响应状态码传递给回调接口
                    listener.loginResponse(code == 200);


                } catch (Exception e) {
                    Log.d("Login Error", e.toString());
                    listener.loginResponse(false);
                }
            }
        }).start();
    }
}