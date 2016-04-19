<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:fmp="http://www.filemaker.com/fmpxmlresult" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLoaction="http://www.pbcore.org/PBCore/PBCoreNamespace.html" exclude-result-prefixes="fmp xsi">
    <!--
    
    Note that metadata may be pulled from filemaker server via this url convention:
        http://10.10.200.28/fmi/xml/FMPXMLRESULT.xml?-db=CUNY_TV_archive&-lay=remoteimport&PBCoreIdentifier::identifier=EWM00105&-find
        replace EWM00105 with the mediaid requested
    
    -->
    <xsl:output encoding="UTF-8" method="xml" version="1.0" indent="yes" omit-xml-declaration="yes"/>
    <xsl:key name="N" match="/fmp:FMPXMLRESULT/fmp:METADATA/fmp:FIELD" use="@NAME"/>
    <xsl:key name="N" match="/fmp:FMPXMLRESULT/fmp:METADATA/fmp:FIELD" use="following-sibling::fmp:FIELD/@NAME"/>
    <xsl:template match="fmp:FMPXMLRESULT">
        <xsl:apply-templates select="fmp:RESULTSET"/>
    </xsl:template>
    <xsl:template match="fmp:FMPXMLRESULT/fmp:RESULTSET">
        <xsl:if test="count(fmp:ROW)>0">
            <resourceset>
                <xsl:for-each select="fmp:ROW">
                    <xsl:variable name="row_pos" select="position()"/>
                    <xsl:variable name="asset_pk">
                        <xsl:value-of select="fmp:COL[count(key('N','asset_serial_pk'))]/fmp:DATA"/>
                    </xsl:variable>
                    <resource>
                        <xsl:attribute name="type">3</xsl:attribute>
                        <keyfield>
                            <xsl:attribute name="ref">8</xsl:attribute>
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreIdentifier_mediaid'))]/fmp:DATA[$row_pos]"/>
                        </keyfield>
                        <!--
                        <collection>
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreTitle::title'))]/fmp:DATA"/>
                        </collection>
                        -->
                        <field>
                            <xsl:attribute name="ref">77</xsl:attribute><!-- assettype -->
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreAssetType::assetType'))]/fmp:DATA[$row_pos]"/>
                        </field>
                        <field>
                            <xsl:attribute name="ref">111</xsl:attribute><!-- titles -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreTitle::title'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreTitle::titleType'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                        <field>
                            <xsl:attribute name="ref">84</xsl:attribute><!-- descriptions -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreDescription::description'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreDescription::descriptionType'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                    </resource>
                </xsl:for-each>
            </resourceset>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
