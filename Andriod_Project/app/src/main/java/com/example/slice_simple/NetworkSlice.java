package com.example.slice_simple;

import com.enq.transceiver.VmpCallback;

import android.app.Activity;
import android.content.Context;
import android.os.Build;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.TextView;

import com.enq.transceiver.TransceiverManager;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;

/**
 * 切片app的主要类
 */
public class NetworkSlice extends Activity {
    //context是Android环境
    @Override
    public Context getApplicationContext() {
        return super.getApplicationContext();
    }
    NetworkUtil networkUtil = null;
    public SimUserGame sug = SimUserGameTester.getINSTANCE().generate();//随机生成用户信息，用于对req设置，其实没用上= =

    private ImageView imgShow;//视频
    /**
     * 系统开始时运行的函数
     * @param savedInstanceState
     */
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        imgShow = findViewById(R.id.img_show);
        NetworkUtil.init(getApplicationContext());
        networkUtil = NetworkUtil.getInstance();
        System.out.println("000");
        //注册网络类型的监听并获取当前网络类型，判断是否是5G
        TextView netWorkTypeView = findViewById(R.id.NetworkType);//显示的TextView
        networkUtil.init_show_NetWorkType(this, netWorkTypeView);
        System.out.println("001");
        //获取网络上下行带宽（与接入基站有关）并展示。
        TextView UpBandWidthView = findViewById(R.id.UpBandwidth);
        networkUtil.getUpBandwidthKbps(UpBandWidthView);
        TextView DownBandWidthView = findViewById(R.id.DownBandwidth);
        networkUtil.getDownBandwidthKbps(DownBandWidthView);
        System.out.println("002");
        //获取网络信号强度并展示。同时注册信号强度监听
//        TextView SignalStrengthView = findViewById(R.id.SignalStrength);
//        Map<String, Integer> SignalStr = networkUtil.init_SignalStrengthCallback(SignalStrengthView);

        //初始化TGPA，从其中获取时延抖动丢包率与运营商信息。
        //这个jar使用icmp的部分里 咋获取时延和抖动丢包率，看看（startLocalMonitor和stopLocalMonitor这两个？ 考虑通过沟通来了解
        //这几段代码可以删掉，目前没用到腾讯的TGPA
        String openid = "";
        TransceiverManager.getInstance().init(openid, "cloud.tgpa.qq.com", getApplicationContext());
        TransceiverManager.getInstance().queryClientRealIpOperatorAndAttribution(new VmpCallback() {
            @Override
            public int notifySystemInfo(String s) {
                System.out.println("ENQSDK" + s);
                return 0;
            }
        });
        //初始化完后进行定时器部分，开始通信
        main();
    }

    /**
     * 一直执行的函数。要求两个网络的监听器都已经成功注册了才开始执行的。
     */
    public void main(){
        //和服务器通信的两个类
        ConnectSer connectSer = new ConnectSer();
        connectSer.init(imgShow);
        ConnectSlice connectSlice = new ConnectSlice(); //主线程里绝对不能socket bind……会闪退

        //开始带宽时延抖动丢包率记录
        networkUtil.init_NetMatrix();
        ArrayList<ArrayDeque<Double>> NetMatrix = new ArrayList<>();//在DEBUG0中用到。
        /*
        真实实验时这么初始化，然后下面四行放在定时器里
        ArrayList<ArrayDeque<Double>> NetMatrix = new ArrayList<>();
        NetMatrix.add(networkUtil.getBandwidth());
        NetMatrix.add(networkUtil.getDelay());
        NetMatrix.add(networkUtil.getJitter());
        NetMatrix.add(networkUtil.getPacketLoss());
        */
        int DEBUG = 1;
        if(DEBUG == 0){//理论上实际工程进入的分支，在这里判断要切片时，直接把获取完网络质量直接通过ConnectSlice发送
            Timer timer = new Timer();
            timer.scheduleAtFixedRate(new TimerTask() {
                @Override
                public void run() {
                    Map<String, Integer> SignalStr = SigStrengthListener.getINSTANCE().getSignalStr();
                    String netType = networkUtil.getNetWorkType();
                    int UpBandWidth = networkUtil.getUpBandwidthKbps(null);
                    int DownBandWidth = networkUtil.getDownBandwidthKbps(null);

                    SignalStr.put("UpBandWidth", UpBandWidth);
                    SignalStr.put("DownBandWidth", DownBandWidth);

                    if("5G".equals(netType)){
                        if(judge_slice_build(NetMatrix, SignalStr, get_demand_model())){//切片触发。具体接口待定，可接入其他网络加速策略。
                            NetMatrix.clear();
                            NetMatrix.add(networkUtil.getBandwidth());
                            NetMatrix.add(networkUtil.getDelay());
                            NetMatrix.add(networkUtil.getJitter());
                            NetMatrix.add(networkUtil.getPacketLoss());
                            System.out.println("NetMatrix:");
                            System.out.println(NetMatrix);
                            HashMap<String, String> sliceMsg = new HashMap();
//                            sliceMsg.put("isp", "中国电信");
                            sliceMsg.put("req", "" + 3);
                            sliceMsg.put("SignalData", SignalStr.toString());
                            //以下四项数据暂时是用已定生成数据。已完成了完整的测量接口，但暂未接入。若接入可略微改写统一下四项数据长度即可。
                            sliceMsg.put("BandWidth", NetMatrix.get(0).toString());
                            sliceMsg.put("Delay", NetMatrix.get(1).toString());
                            sliceMsg.put("Jitter", NetMatrix.get(2).toString());
                            sliceMsg.put("PacketLoss", NetMatrix.get(3).toString());
                            System.out.println("Send sliceMsg to ser");
                            //发送
                        }
                    }
                }
            }, 10000, 60000);//一分钟一次定时判断
        }
        else if (DEBUG == 2){//跑产生数据的过程
            getTestConSer gcs = new getTestConSer();
            getTestConSli gcsl = new getTestConSli();
            Thread thread = new Thread(){
                @Override
                public void run(){
                    gcs.recFile();
                }
            };
            thread.start();
            Timer timer = new Timer();
            timer.scheduleAtFixedRate(new TimerTask() {
                @Override
                public void run(){
                    gcsl.sendSliceMsgToSli();
                }
            }, 15000, 15000);//15s发一次网络状态
        }
        else {//性能测试，进入和渲染服务器的通信过程，同时和切片策略服务器通信
            System.out.println("开始性能测试");
            HashMap<String, String> sliceMsg = new HashMap();
            sliceMsg.put("req", "" + 3);
//现在的实现方式是在这个线程里面循环，所以要传那个时候的网络质量
            Thread threadSer = new Thread(){
                @Override
                public void run(){
                    connectSer.recFile();
                }
            };
            Thread threadSli = new Thread(){
                @Override
                public void run(){
                    connectSlice.startSend();
                }
            }; //定时向切片策略服务器上报网络质量（第一次时切片）
            threadSer.start();
            threadSli.start();
        }
    }



    /**
     * 模块：云游戏业务需求建模
     * 输入：1.根据手机型号转换模拟的码率
     * 2.模拟的游戏类型（用户等级等暂未考虑），作为目前的按需分类结果
     * 通过设备名转化为码率，进而决定切片。暂时将码率需求设置为6 15 30三档？
     */
    public int get_demand_model(){
        String device = Build.MODEL;
        //debug用，显示设备型号
        TextView deviceView = findViewById(R.id.Device);
        deviceView.setText(device);
        //先初始化BitRate，根据设备型号模拟得到分辨率
        SimBitRate.init_BitRate(getApplicationContext());
        if(SimBitRate.getInstance() == null){
            System.out.println("BitRate.getInstance() == null");
        }
        int br = SimBitRate.getInstance().getRate(device) / 1024;//结果是1,6,15,30
        TextView bitrateView = findViewById(R.id.BitRate);
        bitrateView.setText("Bitrate: " + br);

        //简单的计算出一种类别请求。远程会进行调配控制。
        if(br == 1){//根据用户码率（机型分辨率）对画质需求进行修正，当画质需求较低时，相应调整切片类型
            if(sug.gameType == SimUserGame.REQ_BANDWIDTH)
                return SimUserGame.REQ_DEFAULT;
            else if(sug.gameType == SimUserGame.REQ_MOBA)
                return SimUserGame.REQ_DELAY;
        }
        else if(br == 30){//提升画质
            if(sug.gameType == SimUserGame.REQ_DEFAULT)
                return SimUserGame.REQ_BANDWIDTH;
            else if(sug.gameType == SimUserGame.REQ_DELAY)
                return SimUserGame.REQ_MOBA;
        }
        return sug.gameType;
    }

    /**
     *
     * @param NetData [带宽, 时延, 抖动, 丢包率]
     * @param SigData 无线信号强度
     * @param req 切片需求类型
     * @return
     */
    public boolean judge_slice_build(ArrayList<ArrayDeque<Double>>NetData, Map<String, Integer>SigData, int req){
        //无线信号强度 暂未想好怎么用
        int upb = SigData.get("UpBandWidth");
        int downb = SigData.get("DownBandWidth");
        int dbm = SigData.get("dbm");
        //网络测量数据
        ArrayDeque<Double> bd = NetData.get(0);
        ArrayDeque<Double> delay = NetData.get(1);
        ArrayDeque<Double> jitter = NetData.get(2);
        ArrayDeque<Double> pl = NetData.get(3);

        switch (req){
            case 0: //default
                return judgeDeq(delay, 140, false) || judgeDeq(jitter, 50, false) ||
                        judgeDeq(pl, 6, false) || judgeDeq(bd, 5, true);//TODO:依据标准设置
            case 1: //bandwidth
                return judgeDeq(bd, 2000, true);
            case 2: //jitter
                return judgeDeq(delay, 100, false) || judgeDeq(jitter, 16, false) ||
                        judgeDeq(pl, 3, false);
            case 3: //moba
                return judgeDeq(delay, 70, false) || judgeDeq(jitter, 16, false) ||
                        judgeDeq(pl, 3, false) || judgeDeq(bd, 7, true);
        }
        return false;
    }


    /**
     * 统计该网络指标平均值，大于standard的值数量，最大值和最小值等，判断是否满足该类型网络，触发切片。
     * @param deq 双端队列，可以是时延带宽抖动丢包率
     * @param standard 标准要求
     * @param isUp 是否是需要大于standard（如带宽）
     * @return 是否触发切片请求。
     */
    public boolean judgeDeq(ArrayDeque<Double> deq, int standard, boolean isUp){
        double ave = 0, count = 0, doubleCount = 0, maxvalue = 0, minvalue = 999;//可以考虑用方差等统计数据进一步优化
        int len = deq.size();
        for(int i = 0; i < len; ++i){
            double t = deq.getFirst();
            ave += t;
            if(isUp){ // 是带宽来写
                if(t < standard){
                    ++count;
                    if(t < standard / 2){
                        doubleCount++;
                    }
                }
                if(t < minvalue){
                    minvalue = t;
                }
            }else{
                if(t > standard){
                    ++count;
                    if(t > standard * 2){
                        ++doubleCount;
                    }
                }
                if(t > maxvalue){
                    maxvalue = t;
                }
            }
        }
        deq.removeFirst();
        //判断ave, count, value三个值
        return (ave > standard) || (count > len/5) || (doubleCount > len/10);
    }

}


//timer.scheduleAtFixedRate(new TimerTask() {
//            @Override
//            public void run() {//内部另一个原先的方案
//                        NetworkRequest.Builder request = new NetworkRequest.Builder();
//                        request.addTransportType(NetworkCapabilities.TRANSPORT_CELLULAR);
//                        request.addCapability(NetworkCapabilities.NET_CAPABILITY_ENTERPRISE);
//                        ConnectivityManager connection_manager =
//                                (ConnectivityManager) getApplicationContext().getSystemService(Context.CONNECTIVITY_SERVICE);
//                        System.out.println("发起含有切片的NetworkCapability");
//                        connection_manager.registerNetworkCallback(request.build(), new ConnectivityManager.NetworkCallback() {
//                            @Override
//                            public void onAvailable(Network network) {
//                                NetworkCapabilities nc = connection_manager.getNetworkCapabilities(network);
//                                System.out.println("NetworkCapabilities: "+ nc);
//                                connection_manager.bindProcessToNetwork(network);
//                            }
//                        });