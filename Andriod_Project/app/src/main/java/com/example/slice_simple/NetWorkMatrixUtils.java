package com.example.slice_simple;

import android.content.Context;
import android.net.TrafficStats;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Timer;
import java.util.TimerTask;

/**
 * 实时测量带宽，时延，抖动，丢包率；并存储过去两分钟内的数据。
 */
public class NetWorkMatrixUtils {
    private Context context;
    //带宽所需
    private long lastTotalRxBytes = 0; //是该应用的字节数
    private long lastTimeStamp = 0;


    public ArrayDeque<Double> speedHis = new ArrayDeque<>();

    //时延抖动丢包的存储队列
    public ArrayDeque<Double> delayDeq = new ArrayDeque<>();
    public ArrayDeque<Double> jitterDeq = new ArrayDeque<>();
//    public ArrayDeque<Double> plDeq = new ArrayDeque<>();
    private int packSum = 0;
    public int pl = 0;
    public NetWorkMatrixUtils(Context context){
        this.context = context;
    }

    TimerTask task = new TimerTask() {
        @Override
        public void run() {
            showNetSpeed();
        }
    };
    TimerTask task2 = new TimerTask() {
        @Override
        public void run() {
            detect();
        }
    };
    public void startShowNetMatrix(){
        lastTotalRxBytes = getTotalRxBytes();
        lastTimeStamp = System.currentTimeMillis();
        new Timer().schedule(task, 1000, 1000); //1s后启动任务，每1s执行一次
        new Timer().schedule(task2, 1000, 1000); //1s后启动任务，每1s执行一次
    }

    //带宽所需要的方法
    private long getTotalRxBytes() {
        return TrafficStats.getUidRxBytes(context.getApplicationInfo().uid) == TrafficStats.UNSUPPORTED ? 0 :(TrafficStats.getTotalRxBytes()/1024);//转为KB
    }

    private void showNetSpeed() {
        long nowTotalRxBytes = getTotalRxBytes();
        long nowTimeStamp = System.currentTimeMillis();
        long speed = ((nowTotalRxBytes - lastTotalRxBytes) * 1000 / (nowTimeStamp - lastTimeStamp));//毫秒转换
        long speed2 = ((nowTotalRxBytes - lastTotalRxBytes) * 1000 % (nowTimeStamp - lastTimeStamp));//毫秒转换

        lastTimeStamp = nowTimeStamp;
        lastTotalRxBytes = nowTotalRxBytes;
        double speednow = Double.parseDouble(String.valueOf(speed) + "." + String.valueOf(speed2));
        speednow = speednow * 8; // 转换为Mbps
        speedHis.add(speednow);
        if(speedHis.size() > 120){
            speedHis.removeFirst();
        }
        System.out.println("Tag:网络质量 吞吐率:" + speednow + " kbps");
    }


    /**
     * 采用ping方式用ICMP报文探测到服务器的时延和丢包 发送一次
     * @return 丢包率+时延
     */
    public void detect() {
        int lost = 0;
        double delay = 0;
        String aimIp = "192.168.1.4"; //414wifi:192.168.1.108;hust:10.12.48.176;有线:222.20.103.130
        try {
            Process p = Runtime.getRuntime().exec("ping -c " + 1 + " " + aimIp);
            BufferedReader buf = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String str;

            while ((str = buf.readLine()) != null) {
//                System.out.println("In icmp detect:" + str);
                if (str.contains("packet loss")) {
                    int i = str.indexOf("received");
                    int j = str.indexOf("%");
                    lost = Integer.parseInt(str.substring(i + 10, j));
                    if(packSum < 2400) {
                        packSum ++;
                        if(lost == 100) pl ++;
                    }
                    else{
                        if(lost == 100) pl ++;
                        else pl--;
                    }
//                    lost = Double.parseDouble(str.substring(i + 10, j));
                    System.out.println("Tag:网络质量 icmp丢包率:" + lost + "%");
//                    plDeq.add(lost);
//                    if(plDeq.size() > 120){
//                        plDeq.removeFirst();
//                    }
                }
                if (str.contains("avg")) {
                    int i = str.indexOf("/", 20);
                    int j = str.indexOf("/", i + 1);
                    delay = Double.parseDouble(str.substring(i + 1, j));
                    System.out.println("Tag:网络质量 icmp时延:" + delay + "ms");
                    if(delayDeq.size() != 0){
                        double ji = delayDeq.getLast() - delay;
                        if(ji < 0) ji = - ji;
                        jitterDeq.add(ji);
                        if(jitterDeq.size() > 120){
                            jitterDeq.removeFirst();
                        }
                    }
                    delayDeq.add(delay);
                    if(delayDeq.size() > 120){
                        delayDeq.removeFirst();
                    }
                }
            }
        } catch (IOException e) {
            System.out.println(e);
        }
    }

    public ArrayDeque<Double> getSpeedHis(){
        return speedHis;
    }

    public ArrayDeque<Double> getDelayDeq() {
        return delayDeq;
    }

    public ArrayDeque<Double> getJitterDeq() {
        return jitterDeq;
    }

    public ArrayDeque<Double> getPlDeq() {//返回最近2400包的丢包率
        ArrayDeque<Double> plDeq = new ArrayDeque<>();
        plDeq.add((double)pl/packSum);
        return plDeq;
    }

//特定时需要清空历史的指标
    public void setSpeedHis(ArrayDeque<Double> speedHis) {
        this.speedHis = speedHis;
    }

    public void setDelayDeq(ArrayDeque<Double> delayDeq) {
        this.delayDeq = delayDeq;
    }

    public void setJitterDeq(ArrayDeque<Double> jitterDeq) {
        this.jitterDeq = jitterDeq;
    }

    public void setPackSum(int packSum) {
        this.packSum = packSum;
    }

    public void setPl(int pl) {
        this.pl = pl;
    }
}
