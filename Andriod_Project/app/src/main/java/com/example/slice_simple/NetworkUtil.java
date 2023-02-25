package com.example.slice_simple;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;
import android.telephony.CellSignalStrengthNr;
import android.telephony.TelephonyCallback;
import android.telephony.TelephonyManager;
import android.widget.TextView;

import androidx.core.app.ActivityCompat;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * 网络工具类，是对网络连接方式，无线强度监听，带宽四个数据的集成。
 * 初始化设置相应的监听（NetTypeListener和SigStrengthListener）
 * 可获取上下行带宽
 * 通过NetWorkMatrixUtils类获取网络状态矩阵（带宽时延抖动丢包率）
 */
public class NetworkUtil {
    private static Context mContext = null;
    private static NetworkUtil Instance = null;

    private NetTypeListener ntl = null;
    private NetWorkMatrixUtils nmu = null;
    private SigStrengthListener ssl = null;

    public static void init(Context ctx) {
        mContext = ctx;
    }
    private NetworkUtil(){
    }
    public static NetworkUtil getInstance(){
        if(Instance == null){
            Instance = new NetworkUtil();
        }
        return Instance;
    }

    /**
     * nt中显示网络连接方式（WiFi/移动数据（2/3/4/5G））并初始化设置动态监听（利用NetTypeListener）
     * @param activity
     * @param nt
     * @return 网络类型（NONE（未连接或出错），WIFI，以及移动数据对应的整数）
     */
    public String init_show_NetWorkType(Activity activity, TextView nt) {
        String netType = "NONE";

        if (mContext == null) {
            return netType;
        }

        ConnectivityManager conManager = (ConnectivityManager) mContext.getSystemService(Context.CONNECTIVITY_SERVICE);
        //权限：Manifest.permission.ACCESS_NETWORK_STATE
        Network network = conManager.getActiveNetwork();//当前默认网络对象
        if (network == null) {
            return netType;
        }
        NetworkCapabilities networkCapabilities = conManager.getNetworkCapabilities(network);
//        System.out.println("NetworkCapabilities in getNetWorkType:"+ networkCapabilities);
        if (networkCapabilities == null) {
            return netType;
        }

        //注册网络连接方式监听 已测试，可正常运行。
        NetTypeListener.init(activity, mContext);
        ntl = NetTypeListener.getInstance();

        NetworkRequest.Builder builder = null;
        builder = new NetworkRequest.Builder();
        NetworkRequest request = builder.build();
        conManager.registerNetworkCallback(request, ntl);

        //因为想在调用时直接获取并显示一次，因此不仅在监听函数里写，先直接获取一遍
        if (networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
            nt.setText("Network : WiFi");
            return "WiFi";//不确定WIFI_AWARE是否也算WIFI连接
        }

        if (networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) {//移动数据的情况是没法和上面共存的
            //System.out.println("networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)");
            int dataNetworkType = TelephonyManager.NETWORK_TYPE_UNKNOWN;
            TelephonyManager telephonyManager = (TelephonyManager) mContext.getSystemService(Context.TELEPHONY_SERVICE);
            //动态获取权限（高风险权限必需）
            if (ActivityCompat.checkSelfPermission(mContext, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {
                // Consider calling
                //    ActivityCompat#requestPermissions
                // here to request the missing permissions, and then overriding
                //   public void onRequestPermissionsResult(int requestCode, String[] permissions,
                //                                          int[] grantResults)
                // to handle the case where the user grants the permission. See the documentation
                // for ActivityCompat#requestPermissions for more details.
                ActivityCompat.requestPermissions(activity, new String[]{Manifest.permission.READ_PHONE_STATE}, 1);
            }
            dataNetworkType = telephonyManager.getDataNetworkType();

            switch (dataNetworkType) {//判断2-5G
                case TelephonyManager.NETWORK_TYPE_UNKNOWN:
                    netType = "UnKnown";
                    break;
                case TelephonyManager.NETWORK_TYPE_GPRS:
                case TelephonyManager.NETWORK_TYPE_EDGE:
                case TelephonyManager.NETWORK_TYPE_GSM:
                case TelephonyManager.NETWORK_TYPE_CDMA:
                case TelephonyManager.NETWORK_TYPE_1xRTT:
                case TelephonyManager.NETWORK_TYPE_IDEN:
                    netType = "2G";
                    break;
                case TelephonyManager.NETWORK_TYPE_EVDO_0:
                case TelephonyManager.NETWORK_TYPE_EVDO_A:
                case TelephonyManager.NETWORK_TYPE_EVDO_B:
                case TelephonyManager.NETWORK_TYPE_EHRPD:
                case TelephonyManager.NETWORK_TYPE_HSUPA:
                case TelephonyManager.NETWORK_TYPE_HSDPA:
                case TelephonyManager.NETWORK_TYPE_HSPA:
                case TelephonyManager.NETWORK_TYPE_HSPAP:
                case TelephonyManager.NETWORK_TYPE_UMTS:
                case TelephonyManager.NETWORK_TYPE_TD_SCDMA:
                    netType = "3G";
                    break;
                case TelephonyManager.NETWORK_TYPE_LTE:
                case TelephonyManager.NETWORK_TYPE_IWLAN:
                    netType = "4G";
                    break;
                case TelephonyManager.NETWORK_TYPE_NR:
                    netType = "5G";
                    break;
                default:
                    netType = "Not Clear";
            }
            nt.setText("Network: cell, " + netType);
        }
        return netType;
    }

    /**
     * 初始化后即时获取网络连接方式的函数，
     */
    public String getNetWorkType(){
        if(ntl == null){
            return null;
        }
        return ntl.getNetType();
    }
    /**
     * 获取到基站的理论下行带宽
     * @param dbv 可以不要，ui显示，仅debug用
     * @return 下行带宽
     */
    public int getDownBandwidthKbps(TextView dbv) {
        ConnectivityManager conManager = (ConnectivityManager) mContext.getSystemService(Context.CONNECTIVITY_SERVICE);
        //权限：Manifest.permission.ACCESS_NETWORK_STATE
        Network network = conManager.getActiveNetwork();//当前默认网络对象
        if (network == null) {
            return 0;
        }
        NetworkCapabilities networkCapabilities = conManager.getNetworkCapabilities(network);
        if (networkCapabilities == null) {
            return 0;
        }
        int res = networkCapabilities.getLinkDownstreamBandwidthKbps();
        if(dbv != null){
            dbv.setText("Down Bandwidth: " + String.valueOf(res) + " kbps");
        }
        return res;
    }

    /**
     * 获取到基站的理论上行带宽
     * @param ubv 可以不要，ui显示，仅debug用
     * @return 上行带宽
     */
    public int getUpBandwidthKbps(TextView ubv) {
        ConnectivityManager conManager = (ConnectivityManager) mContext.getSystemService(Context.CONNECTIVITY_SERVICE);
        //权限：Manifest.permission.ACCESS_NETWORK_STATE
        Network network = conManager.getActiveNetwork();//当前默认网络对象
        if (network == null) {
            return 0;
        }
        NetworkCapabilities networkCapabilities = conManager.getNetworkCapabilities(network);
        if (networkCapabilities == null) {
            return 0;
        }
        int res = networkCapabilities.getLinkUpstreamBandwidthKbps();
        if(ubv != null){
            ubv.setText("Up Bandwidth: " + String.valueOf(res) + " kbps");
        }
        return res;
    }


    /**
     * 获取无线信号强度并监听
     * 注册网络监听，获取rsrp,rsrq和dbm存在map里，用getSignalStrength获取
     * @param ssv
     */
    public Map<String, Integer> init_SignalStrengthCallback(TextView ssv) {
        TelephonyManager telephonyManager = (TelephonyManager) mContext.getSystemService(Context.TELEPHONY_SERVICE);
        //注册监听
        ssl = SigStrengthListener.getINSTANCE();
        telephonyManager.registerTelephonyCallback(new ThreadPoolExecutor(1, 10,
                1, TimeUnit.SECONDS, new LinkedBlockingDeque<Runnable>(10)), ssl);
        System.out.println("010");
        List<CellSignalStrengthNr> strengthNrList = telephonyManager.getSignalStrength().getCellSignalStrengths(CellSignalStrengthNr.class);
//        System.out.println("strengthNrList" + strengthNrList);
        System.out.println("011");
        ssv.setText("Signal Strength: " + strengthNrList);
        Map<String, Integer> res = new HashMap<>();
        System.out.println("012");
        if (!strengthNrList.isEmpty()) {
            CellSignalStrengthNr css = strengthNrList.get(0);
            int dbm = css.getDbm();
            res.put("dbm", dbm);
            System.out.println("dbm: " + dbm);
            int ssRsrp = css.getSsRsrp();
            int ssRsrq = css.getSsRsrq();
            System.out.println("ssRsrp:" + ssRsrp);//csi是信道状态信息，ss是同步信息这样 csi获取的总是错误值（最大 最小）
            System.out.println("ssRsrq:" + ssRsrq);
            res.put("ssRsrp", ssRsrp);
            res.put("ssRsrq", ssRsrq);
        }
        System.out.println("013");
        return res;
    }

    public Map<String, Integer> getSignalStrength() {
        return ssl.getSignalStr();
    }

    /**
     * 借助NetWorkMatrixUtils工具实现对带宽的探测与存储
     */
    public void init_NetMatrix() {
        nmu = new NetWorkMatrixUtils(mContext);
        nmu.startShowNetMatrix();
    }

    public ArrayDeque<Double> getBandwidth(){
        return nmu.getSpeedHis();
    }

    public ArrayDeque<Double> getDelay(){
        return nmu.getDelayDeq();
    }

    public ArrayDeque<Double> getJitter(){
        return nmu.getJitterDeq();
    }

    public ArrayDeque<Double> getPacketLoss(){
        return nmu.getPlDeq();
    }

    public void emptyBandwidth(){
        nmu.setSpeedHis(new ArrayDeque<>());
    }
    public void emptyDelay(){
        nmu.setDelayDeq(new ArrayDeque<>());
    }
    public void emptyJitter(){
        nmu.setJitterDeq(new ArrayDeque<>());
    }
    public void emptyPacketLoss(){
        nmu.setPackSum(0);
        nmu.setPl(0);
    }
}


/*
    public Map<String, Integer> querySignalStrength(TextView ssv) {

        TelephonyManager telephonyManager = (TelephonyManager) mContext.getSystemService(Context.TELEPHONY_SERVICE);
        TelephonyCallback ssl = new SigStrengthListener();

        //注册监听
        telephonyManager.registerTelephonyCallback(new ThreadPoolExecutor(1, 10,
                1, TimeUnit.SECONDS, new LinkedBlockingDeque<Runnable>(10)), ssl);

        Map<String, Integer> queryRes = ((SigStrengthListener)ssl).getSignalStr();
        queryRes = ((SigStrengthListener)ssl).getSignalStr();
        ssv.setText("Query Net: " + queryRes);
        return queryRes;
    }
*/
    /**
     * 获取信号强度 networkCapabilities.getSignalStrength
     * @param ssv 可以不要，仅显示时debug用
     * @return 信号强度
     * 测试结果：不可用！会返回Integer.MIN_VALUE
     */
    /*
    @Deprecated
    public int getSigStrength(TextView ssv) {
        ConnectivityManager conManager = (ConnectivityManager) mContext.getSystemService(Context.CONNECTIVITY_SERVICE);
        //权限：Manifest.permission.ACCESS_NETWORK_STATE
        Network network = conManager.getActiveNetwork();//当前默认网络对象
        if (network == null) {
            return 0;
        }
        NetworkCapabilities networkCapabilities = conManager.getNetworkCapabilities(network);
        if (networkCapabilities == null) {
            return 0;
        }
        int res = networkCapabilities.getSignalStrength();
        ssv.setText("Signal Strength: " + String.valueOf(res));
        return res;
    }
    */


    /**
     * 使用getAllCellInfo获取cellinfo的列表
     * 测试结果：不可用！allCellInfo（cellinfo的列表）包含数量为0
     */
    /*
    @Deprecated
    public void testCellInfo2(Activity act) {
        TelephonyManager telephonyManager = (TelephonyManager) mContext.getSystemService(Context.TELEPHONY_SERVICE);
        if (ActivityCompat.checkSelfPermission(act, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {

            //    ActivityCompat#requestPermissions
            // here to request the missing permissions, and then overriding
            //   public void onRequestPermissionsResult(int requestCode, String[] permissions,
            //                                          int[] grantResults)
            // to handle the case where the user grants the permission. See the documentation
            // for ActivityCompat#requestPermissions for more details.
            ActivityCompat.requestPermissions(act, new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, 1);
        }
        System.out.println("Get ACCESS_FINE_LOCATION Permission");
        List<CellInfo> allCellInfo = telephonyManager.getAllCellInfo();
//        if(allCellInfo != null) System.out.println(allCellInfo.size());
        if (allCellInfo != null && allCellInfo.size() > 0) {
            System.out.println(allCellInfo.size());
            CellInfo info = allCellInfo.get(0);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                // 5G
                if (info instanceof CellInfoNr) {
                    System.out.println("Get CellInfo Nr");
                    CellIdentityNr nr = (CellIdentityNr) ((CellInfoNr) info)
                            .getCellIdentity();
                    CellSignalStrengthNr nrStrength = (CellSignalStrengthNr) ((CellInfoNr) info)
                            .getCellSignalStrength();
                    String RsRp = "-" + nrStrength.getSsRsrp() + "";
                    System.out.println(RsRp);
                }
            }
        }
    }
}
*/





