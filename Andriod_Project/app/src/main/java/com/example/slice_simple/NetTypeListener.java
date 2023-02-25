package com.example.slice_simple;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.telephony.TelephonyManager;

import androidx.core.app.ActivityCompat;

/**
 * 动态监视网络连接（移动数据(2-5G)或wifi）通过getNetType动态获取网络结果。
 * @author: 75939
 * @date: 2022/4/14
 */
public class NetTypeListener extends ConnectivityManager.NetworkCallback {

    private static NetTypeListener Instance = null;
    private static Context mContext = null;
    private static Activity mActivity = null;
    public String netType = "UnKnown";

    public String getNetType() {
        return netType;
    }

    public static void init(Activity act, Context ct){
        mActivity = act;
        mContext = ct;
    }
    private NetTypeListener(){

    }

    public static NetTypeListener getInstance(){
        if(Instance == null){
            Instance = new NetTypeListener();
        }
        return Instance;
    }

    @Override
    public void onAvailable(Network network) {
        super.onAvailable(network);
        System.out.println("on Available 网络已连接");
    }

    @Override
    public void onLost(Network network) {
        super.onLost(network);
        System.out.println("on Available 网络已断开");
    }


    public void onCapabilitiesChanged(Network network, NetworkCapabilities networkCapabilities) {
        super.onCapabilitiesChanged(network, networkCapabilities);

        if(networkCapabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)){
            if(networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)){
       //         System.out.println("Wifi连接中");//TODO:取消注释
                netType = "WiFi";
            }
            else if(networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)){
                System.out.println("移动数据连接中");
                int dataNetworkType = TelephonyManager.NETWORK_TYPE_UNKNOWN;
                TelephonyManager telephonyManager = (TelephonyManager) mContext.getSystemService(Context.TELEPHONY_SERVICE);
                // TelephonyCallback MyPhoneListener = new TelephonyCallback();  监听？？
                // MyPhoneListener.toString();
                //动态获取权限（高风险权限必需）
                if (ActivityCompat.checkSelfPermission(mContext, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {
                    // Consider calling
                    //    ActivityCompat#requestPermissions
                    // here to request the missing permissions, and then overriding
                    //   public void onRequestPermissionsResult(int requestCode, String[] permissions,
                    //                                          int[] grantResults)
                    // to handle the case where the user grants the permission. See the documentation
                    // for ActivityCompat#requestPermissions for more details.
                    ActivityCompat.requestPermissions(mActivity, new String[]{Manifest.permission.READ_PHONE_STATE}, 1);
                }
                dataNetworkType = telephonyManager.getDataNetworkType();

                switch (dataNetworkType) {//判断2-5G
                    case TelephonyManager.NETWORK_TYPE_UNKNOWN:
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
            }
        }
    }
}
