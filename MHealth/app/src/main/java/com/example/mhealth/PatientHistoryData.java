package com.example.mhealth;

public class PatientHistoryData {
    private Integer id;
    private String result;
    private String time;
    private String detail;
    private String comment;

    public PatientHistoryData(Integer id, String result, String time, String detail, String comment) {
        this.id = id;
        this.result = result;
        this.time = time;
        this.detail = detail;
        this.comment = comment;
    }

    public Integer getId() {
        return id;
    }

    public String getResult() {
        return result;
    }

    public String getTime() {
        return time;
    }

    public String getDetail() {
        return detail;
    }

    public String getComment() {
        return comment;
    }
}
