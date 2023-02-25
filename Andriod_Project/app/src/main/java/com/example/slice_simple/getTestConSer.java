package com.example.slice_simple;

import static java.lang.Math.min;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;

/**
 * 获取训练数据时与服务器通信的函数
 */
public class getTestConSer {
    public Map<String, String> data = new HashMap<>();

    public Map<String, String> getData() {
        return data;
    }
    public void setData(Map<String, String> data) {
        this.data = data;
    }


    public void recFile(){
        Socket socket = null;
        try {
            String aimIp = "192.168.1.105";//222.20.96.38 192.168.166.189  112.74.104.115
            int port = 5051;
            System.out.println("Tag:训练数据获取 正在与渲染服务器建立连接：" + aimIp + " "  + port);
            socket = new Socket(aimIp, port);
            if(socket.isConnected())
                System.out.println("Tag:训练数据获取 " + aimIp + " "  + port + " " + "Connect success!");

            //接收文件长度
            byte[] bytes = new byte[4];
            InputStream is = socket.getInputStream();
            is.read(bytes);
            //解码pack的字节
            byte[] bytes2 = new byte[4];
            for(int i = 0; i < 4; ++i) //不逆转解码不出来我是服了
                bytes2[i] = bytes[3-i];
            ByteBuffer firstLine = ByteBuffer.wrap(bytes2);
            int fileLen = firstLine.getInt();
            System.out.println("Tag:训练数据获取 传输文件大小：" + fileLen + " B"); //就输出一次，剩下的循环里不输出了

            for(int i = 1; i <= 50; ++i) {
                long startTime = System.currentTimeMillis();//计算通信用时
                InputStreamReader isr = new InputStreamReader(
                        is, "gb2312");
                char[] buf = new char[1024];//统计回传字节kb数
                int count = fileLen;
                int t = 0;
                while ((t = isr.read(buf, 0, min(buf.length, count))) > 0) {
                    count -= t;
                }
                //远端发完文件后会关闭socket，重新连接
                isr.close();
                is.close();
                socket.close();
                if(i < 50){
                    socket = new Socket(aimIp, port);
                    is = socket.getInputStream();
                    is.read(bytes);
                }
            }
        }
        catch (IOException e) {
            System.out.println(e);
        }
    }
}
