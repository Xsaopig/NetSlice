package com.example.slice_simple;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * 与服务器进行四次通信以打标的算法 通过训练感知该网络质量和需求的用户倾向于被分配什么资源
 */
public class getTestConSli {
    NetworkUtil networkUtil = NetworkUtil.getInstance();
    /**
     * 发送信息给策略控制器器的。data是要发送的信息
     */
    public void sendSliceMsgToSli(){
        Socket socket = null;
        Map<String, String> data = new HashMap<>();
        //414wifi:192.168.1.108;hust:10.12.48.176;有线:222.20.103.130
        try {
            //发送请求与QoE
            System.out.println("Tag:训练数据获取 发送当前网络质量并更新切片类型");
            ArrayList<ArrayDeque<Double>> NetMatrix = new ArrayList<>();
            NetMatrix.add(networkUtil.getBandwidth());
            NetMatrix.add(networkUtil.getDelay());
            NetMatrix.add(networkUtil.getJitter());
            NetMatrix.add(networkUtil.getPacketLoss());
            String req = "1";
            data.put("req", req); //在这里修改终端需求类型
            data.put("BandWidth", NetMatrix.get(0).toString());
            data.put("Delay", NetMatrix.get(1).toString());
            data.put("Jitter", NetMatrix.get(2).toString());
            data.put("PacketLoss", NetMatrix.get(3).toString());
            String aimIp = "192.168.1.105";//记得改ip
            int port = 5050;
            socket = new Socket(aimIp, port);
            System.out.println("Tag:训练数据获取 与策略服务器连接成功");
            BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream()));
            bw.write(data.toString());
            for(int i = 0; i < 10000; ++i)
                bw.flush();
            socket.close();
            networkUtil.emptyBandwidth();
            networkUtil.emptyDelay();
            networkUtil.emptyJitter();
            networkUtil.emptyPacketLoss();
        }
        catch (IOException e) {
            System.out.println(e);
        }
    }
}
