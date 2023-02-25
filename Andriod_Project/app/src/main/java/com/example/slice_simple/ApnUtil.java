package com.example.slice_simple;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.Settings;
import android.telephony.TelephonyManager;

/**
 * 考虑通过APN设置切片类型，从而使用安卓支持的无线侧切片。
 * 但安卓本身并未实现，
 * 且APN操作的权限要求等级太高，系统级应用，因此废弃
 */

@Deprecated
public class ApnUtil {
    public static Uri APN_URI = Uri.parse("content://telephony/carriers");
    public static Uri CURRENT_APN_URI = Uri.parse("content://telephony/carriers/preferapn");

    public static int addAPN(Context context, String apn) {
        int id = -1;
        String NUMERIC = getSIMInfo(context);
        if (NUMERIC == null) {
            return -1;
        }

        ContentResolver resolver = context.getContentResolver();
        ContentValues values = new ContentValues();
        values.put("name", apn);                                  //apn中文描述
        values.put("apn", apn);                                     //apn名称
        values.put("type", "default");                            //apn类型
        values.put("numeric", NUMERIC);
        values.put("mcc", NUMERIC.substring(0, 3));
        values.put("mnc", NUMERIC.substring(3, NUMERIC.length()));
        values.put("proxy", "");                                        //代理
        values.put("port", "");                                         //端口
        values.put("mmsproxy", "");                                     //彩信代理
        values.put("mmsport", "");                                      //彩信端口
        values.put("user", "");                                         //用户名
        values.put("server", "");                                       //服务器
        values.put("password", "");                                     //密码
        values.put("mmsc", "");                                          //MMSC
        Cursor c = null;
        Uri newRow = resolver.insert(APN_URI, values);
        if (newRow != null) {
            c = resolver.query(newRow, null, null, null, null);
            int idIndex = c.getColumnIndex("_id");
            c.moveToFirst();
            id = c.getShort(idIndex);
        }
        if (c != null)
            c.close();
        return id;
    }

    public static String getSIMInfo(Context context) {
        TelephonyManager iPhoneManager = (TelephonyManager)context
                .getSystemService(Context.TELEPHONY_SERVICE);
        return iPhoneManager.getSimOperator();
    }

    // 设置接入点
    public static void setAPN(Context context, int id) {
        ContentResolver resolver = context.getContentResolver();
        ContentValues values = new ContentValues();
        values.put("apn_id", id);
        resolver.update(CURRENT_APN_URI, values, null, null);
    }


    public static int getAPN(Context context) {
        System.out.println("Enter getAPN");
        ContentResolver resolver = context.getContentResolver();
        Cursor c = resolver.query(CURRENT_APN_URI, null, null, null, null);

        System.out.println("Finish query");
        c.moveToFirst();

        // 该项APN存在

        if (c != null && c.moveToNext()) {
            int id = 0, idx1, idx2, idx3;
            String name1 = "", apn1 = "";
            if((idx1 = c.getColumnIndex("_id")) >= 0){
                id = c.getShort(idx1);
            }
            if((idx2 = c.getColumnIndex("name")) >= 0){
                name1 = c.getString(idx2);
            }
            if((idx3 = c.getColumnIndex("apn")) >= 0){
                apn1 = c.getString(idx3);
            }
            System.out.println("APN has exist: " + id + name1 + apn1);
            return id;
        }
        c.close();
        /**/
        return -1;
    }

}
