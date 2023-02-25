package com.example.slice_simple;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;

/**
 * 发送信息给策略服务器的类。data是要发送的信息
 */
public class ConnectSlice{
    NetworkUtil networkUtil = NetworkUtil.getInstance();
    Map<String, String> data = new HashMap<>();
    Socket socket = null;
    String aimIp = "192.168.1.2";
    int port = 5050;

    /**
     * 定时向策略服务器上报网络状态（第一次时顺便切片），实验用
     */
    public void startSend(){
        try {
            socket = new Socket(aimIp, port);
        }
        catch (IOException e) {
            System.out.println("和切片策略服务器通信失败");
            System.out.println(e);
        }
        boolean isFirst = true;
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                if (isFirst){
                    sendSliceMsgToSli("1");
                }
                else{
                    sendSliceMsgToSli("0");
                }
            }
        }, 15000, 15000);//一分钟一次定时判断
    }

    /**
     * 向策略服务器发送信息
     * @param tp
     */
    public void sendSliceMsgToSli(String tp){
        //414wifi:192.168.1.108;hust:10.12.48.176;有线:222.20.103.130
        try {
            //准备网络质量数据
            data.put("type", tp);
            data.put("req", "" + 3);
            ArrayList<ArrayDeque<Double>> NetMatrix = new ArrayList<>();
            NetMatrix.add(networkUtil.getBandwidth());
            NetMatrix.add(networkUtil.getDelay());
            NetMatrix.add(networkUtil.getJitter());
            NetMatrix.add(networkUtil.getPacketLoss());
            data.put("BandWidth", NetMatrix.get(0).toString());
            data.put("Delay", NetMatrix.get(1).toString());
            data.put("Jitter", NetMatrix.get(2).toString());
            data.put("PacketLoss", NetMatrix.get(3).toString());

            System.out.println("Tag:性能测试 正在与切片策略控制器建立连接：" + aimIp + " "  + port);
            if(socket.isConnected())
                System.out.println("Tag:性能测试 " + aimIp + " "  + port + " " + "Connect success!");
//            System.out.println("Tag:data " + data);
            BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream()));
            bw.write(data.toString() + "END");
            System.out.println("Tag:网络质量 " + "发送data：" + data.toString());
            for(int i = 0; i < 100000; ++i)
            bw.flush();
            //问题在于这里获取完网络质量后没有清空
            networkUtil.emptyDelay();
            networkUtil.emptyBandwidth();
            networkUtil.emptyJitter();
            networkUtil.emptyPacketLoss();
        }
        catch (IOException e) {
            System.out.println(e);
        }
    }
    public void closeSocket(){
        try{
            socket.close();
        }
        catch (IOException e) {
            System.out.println(e);
        }
    }
    /*

    public void sendNetMsgToSli(){
        Socket socket = null;
        Map<String, String> data = new HashMap<>();
        data.put("type", "0");
        //414wifi:192.168.1.108;hust:10.12.48.176;有线:222.20.103.130
        try {
            //准备网络质量数据
            NetworkUtil networkUtil = NetworkUtil.getInstance();
            ArrayList<ArrayDeque<Double>> NetMatrix = new ArrayList<>();
            NetMatrix.add(networkUtil.getBandwidth());
            NetMatrix.add(networkUtil.getDelay());
            NetMatrix.add(networkUtil.getJitter());
            NetMatrix.add(networkUtil.getPacketLoss());
            data.put("BandWidth", NetMatrix.get(0).toString());
            data.put("Delay", NetMatrix.get(1).toString());
            data.put("Jitter", NetMatrix.get(2).toString());
            data.put("PacketLoss", NetMatrix.get(3).toString());
            String aimIp = "192.168.1.107";
            int port = 5050;
            System.out.println("Tag:性能测试 正在与切片策略控制器建立连接：" + aimIp + " "  + port);
            socket = new Socket(aimIp, port);
            if(socket.isConnected())
                System.out.println("Tag:性能测试 " + aimIp + " "  + port + " " + "Connect success!");
//            System.out.println("Tag:data " + data);
            BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream()));
            bw.write(data.toString());
            for(int i = 0; i < 100000; ++i)
                bw.flush();
            socket.close();
        }
        catch (IOException e) {
            System.out.println(e);
        }
    }
     */
}
