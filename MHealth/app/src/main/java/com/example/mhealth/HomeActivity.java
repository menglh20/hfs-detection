package com.example.mhealth;

import android.os.Bundle;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;

import com.google.android.material.bottomnavigation.BottomNavigationView;

public class HomeActivity extends AppCompatActivity {
    private String username;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);
        username = getIntent().getStringExtra("USERNAME");
        BottomNavigationView bottomNavigationView = findViewById(R.id.bottom_navigation);

        // 设置底部导航栏的监听器
        bottomNavigationView.setOnNavigationItemSelectedListener(item -> {
            if (item.getItemId() == R.id.navigation_detect) {
                // 切换到“检测”界面
                DetectFragment detectFragment = DetectFragment.newInstance(username);
                getSupportFragmentManager().beginTransaction()
                        .replace(R.id.fragment_container, detectFragment)
                        .commit();
                return true;
            } else if (item.getItemId() == R.id.navigation_history) {
                // 切换到“历史”界面
                HistoryFragment historyFragment = HistoryFragment.newInstance(username);
                getSupportFragmentManager().beginTransaction()
                        .replace(R.id.fragment_container, historyFragment)
                        .commit();
                return true;
            }
            return false;
        });

        // 默认显示“检测”界面
        DetectFragment detectFragment = DetectFragment.newInstance(username);
        getSupportFragmentManager().beginTransaction()
                .replace(R.id.fragment_container, detectFragment)
                .commit();
    }
}
