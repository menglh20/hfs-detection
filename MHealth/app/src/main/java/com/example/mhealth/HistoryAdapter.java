package com.example.mhealth;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.mhealth.PatientHistoryData;

import java.util.List;

public class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.HistoryViewHolder> {

    private List<PatientHistoryData> historyDataList;

    public HistoryAdapter(List<PatientHistoryData> historyDataList) {
        this.historyDataList = historyDataList;
    }

    @NonNull
    @Override
    public HistoryViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        // 创建 ViewHolder 实例，加载单个 item 的布局
        View itemView = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_history, parent, false);
        return new HistoryViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull HistoryViewHolder holder, int position) {
        // 绑定数据到 ViewHolder
        PatientHistoryData historyData = historyDataList.get(position);
        holder.bind(historyData);
    }

    @Override
    public int getItemCount() {
        return historyDataList.size();
    }

    // ViewHolder 类，用于持有单个 item 的视图
    public static class HistoryViewHolder extends RecyclerView.ViewHolder {

        private TextView idTextView;
        private TextView resultTextView;
        private TextView timeTextView;
        private TextView detailTextView;
        private TextView commentTextView;

        public HistoryViewHolder(@NonNull View itemView) {
            super(itemView);
            // 初始化视图
            idTextView = itemView.findViewById(R.id.idTextView);
            resultTextView = itemView.findViewById(R.id.resultTextView);
            timeTextView = itemView.findViewById(R.id.timeTextView);
            detailTextView = itemView.findViewById(R.id.detailTextView);
            commentTextView = itemView.findViewById(R.id.commentTextView);
        }

        public void bind(PatientHistoryData historyData) {
            // 将数据绑定到视图中的各个 TextView
            idTextView.setText(historyData.getId().toString());
            resultTextView.setText(historyData.getResult());
            timeTextView.setText(historyData.getTime());
            detailTextView.setText(historyData.getDetail());
            commentTextView.setText(historyData.getComment());
        }
    }
}
