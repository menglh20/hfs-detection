package com.example.mhealth;

import android.os.Bundle;

import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;

public class HistoryFragment extends Fragment {
    private HistoryAdapter adapter;
    private List<PatientHistoryData> historyList;
    private String username;

    public HistoryFragment() {
        // Required empty public constructor
    }

    // 静态的 newInstance 方法，用于传递用户名参数
    public static HistoryFragment newInstance(String username) {
        HistoryFragment fragment = new HistoryFragment();
        Bundle args = new Bundle();
        args.putString("USERNAME", username);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 获取传递过来的用户名
        if (getArguments() != null) {
            username = getArguments().getString("USERNAME");
        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_history, container, false);
        TextView welcomeText = view.findViewById(R.id.welcome_text);
        welcomeText.setText(username + "的历史记录:");
        RecyclerView recyclerView = view.findViewById(R.id.recyclerView);
        historyList = new ArrayList<>();
        adapter = new HistoryAdapter(historyList);
        recyclerView.setLayoutManager(new LinearLayoutManager(getContext()));
        recyclerView.setAdapter(adapter);
        loadPatientHistory(username); // 调用接口加载历史数据
        return view;
    }

    public interface ApiResponseListener {
        void fetchDataFinished(boolean isSuccessful, List<PatientHistoryData> detectResults);
    }

    private void updateHistoryList(List<PatientHistoryData> detectResults) {
        historyList.clear();
        historyList.addAll(detectResults);

        // 只展示前10条历史记录
        if (historyList.size() > 10) {
            historyList = historyList.subList(0, 10);
        }

        adapter.notifyDataSetChanged();
    }

    private void loadPatientHistory(String username) {
        fetchDataFromApi(username, new ApiResponseListener() {
            @Override
            public void fetchDataFinished(boolean isSuccessful, List<PatientHistoryData> detectResults) {
                if (isSuccessful) {
                    updateHistoryList(detectResults);
                }
            }
        });
    }

    private void fetchDataFromApi(String username, ApiResponseListener listener) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL("http://" + getResources().getText(R.string.ip_address) + "/api/detect/history/");

                    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                    connection.setRequestMethod("POST");
                    connection.setDoOutput(true);

                    Log.d("HistoryFragment", "Request: " + username);

                    // 设置请求体参数
                    String params = "name=" + URLEncoder.encode(username, "UTF-8");
                    connection.setDoOutput(true);
                    OutputStream outputStream = connection.getOutputStream();
                    outputStream.write(params.getBytes());
                    outputStream.flush();
                    outputStream.close();

                    // 获取服务器响应状态码
                    int responseCode = connection.getResponseCode();
                    Log.d("HistoryFragment", "Response code: " + responseCode);

                    if (responseCode != 200) {
                        Log.d("HistoryFragment", connection.getInputStream().toString());
                        listener.fetchDataFinished(false, null);
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
                    Log.d("HistoryFragment", responseBody);
                    JSONObject jsonResponse = new JSONObject(responseBody);
                    List<PatientHistoryData> detectResults = new ArrayList<>();
                    for (int i = 0; i < jsonResponse.getJSONArray("results").length(); i++) {
                        JSONObject data = jsonResponse.getJSONArray("results").getJSONObject(i);
                        detectResults.add(new PatientHistoryData(
                                i + 1,
                                data.getString("result"),
                                data.getString("time"),
                                data.getString("detail"),
                                data.getString("comment")
                        ));
                    }
                    getActivity().runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            listener.fetchDataFinished(true, detectResults);
                        }
                    });

                } catch (Exception e) {
                    Log.d("HistoryFragment", "Error: " + e.getMessage());
                    listener.fetchDataFinished(false, null);
                }
            }
        }).start();
    }
}