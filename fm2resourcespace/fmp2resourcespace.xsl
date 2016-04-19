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
        <resourceset>
            <xsl:for-each select="fmp:ROW">
            <xsl:variable name="row_pos" select="position()"/>
            <xsl:variable name="asset_pk">
                <xsl:value-of select="fmp:COL[count(key('N','asset_serial_pk'))]/fmp:DATA"/>
            </xsl:variable>
            <resource>
                <xsl:attribute name="type">3</xsl:attribute>
                <keyfield>
                    <xsl:attribute name="type">8</xsl:attribute>
                    <xsl:value-of select="fmp:COL[count(key('N','PBCoreIdentifier_mediaid'))]/fmp:DATA[$row_pos]"/>
                </keyfield>
                <collection>
                    <xsl:value-of select="fmp:COL[count(key('N','PBCoreTitle::title'))]/fmp:DATA"/>
                </collection>
                <field>
                    <xsl:attribute name="type">77</xsl:attribute><!-- assettype -->
                    <xsl:value-of select="fmp:COL[count(key('N', 'PBCoreAssetType::assetType'))]/fmp:DATA[$row_pos]"/>
                </field>
                <field>
                    <xsl:attribute name="type">73</xsl:attribute><!-- assettype -->
                    <xsl:variable name="rows">
                        <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreTitle::title'))]/fmp:DATA">
                            <xsl:variable name="pos" select="position()"/>
                            <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                    <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreTitle::titleType'))]/fmp:DATA[$pos]"/>
                            <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                    <xsl:value-of select="."/>
                            <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        </xsl:for-each>
                    </xsl:variable>
                    <xsl:if test="$rows">
                        <xsl:text>&lt;table&gt;&lt;tr&gt;&lt;th&gt;Type&lt;/th&gt;&lt;/tr&gt;&lt;tr&gt;&lt;th&gt;Title&lt;/th&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:copy-of select="$rows"/>
                        <xsl:text>&lt;/table&gt;</xsl:text>
                    </xsl:if>
                </field>
                <field>
                    <xsl:attribute name="type">8</xsl:attribute>
                    <xsl:value-of select="fmp:COL[count(key('N', 'PBCoreAssetType::assetType'))]/fmp:DATA[$row_pos]"/>
                </field>
                    <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreIdentifier::asset_serial_fk'))]/fmp:DATA">
                        <xsl:variable name="pos" select="position()"/>
                        <xsl:variable name="asset_fk"><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreIdentifier::asset_serial_fk'))]/fmp:DATA[$pos]"/></xsl:variable>
                        <xsl:if test="$asset_fk=$asset_pk">
                            <pbcoreIdentifier>
                                <identifier><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreIdentifier::identifier'))]/fmp:DATA[$pos]"/></identifier>
                                <identifierSource><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreIdentifier::identifierSource'))]/fmp:DATA[$pos]"/></identifierSource>
                            </pbcoreIdentifier>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreTitle::asset_serial_fk'))]/fmp:DATA">
                        <xsl:variable name="pos" select="position()"/>
                        <xsl:variable name="asset_fk"><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreTitle::asset_serial_fk'))]/fmp:DATA[$pos]"/></xsl:variable>
                        <xsl:if test="$asset_fk=$asset_pk">
                            <pbcoreTitle>
                                <title><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreTitle::title'))]/fmp:DATA[$pos]"/></title>
                                <titleType><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreTitle::titleType'))]/fmp:DATA[$pos]"/></titleType>
                            </pbcoreTitle>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreSubject::asset_serial_fk'))]/fmp:DATA">
                        <xsl:variable name="pos" select="position()"/>
                        <xsl:variable name="asset_fk"><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreSubject::asset_serial_fk'))]/fmp:DATA[$pos]"/></xsl:variable>
                        <xsl:if test="$asset_fk=$asset_pk">
                            <pbcoreSubject>
                                <subject><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreSubject::subject'))]/fmp:DATA[$pos]"/></subject>
                                <subjectAuthorityUsed><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreSubject::subjectAuthorityUsed'))]/fmp:DATA[$pos]"/></subjectAuthorityUsed>
                            </pbcoreSubject>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreDescription::asset_serial_fk'))]/fmp:DATA">
                        <xsl:variable name="pos" select="position()"/>
                        <xsl:variable name="asset_fk"><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreDescription::asset_serial_fk'))]/fmp:DATA[$pos]"/></xsl:variable>
                        <xsl:if test="$asset_fk=$asset_pk">
                            <pbcoreDescription>
                                <description><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreDescription::description'))]/fmp:DATA[$pos]"/></description>
                                <descriptionType><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreDescription::descriptionType'))]/fmp:DATA[$pos]"/></descriptionType>
                            </pbcoreDescription>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreInstantiation::asset_serial_fk'))]/fmp:DATA">
                        <xsl:variable name="pos" select="position()"/>
                        <xsl:variable name="asset_fk"><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::asset_serial_fk'))]/fmp:DATA[$pos]"/></xsl:variable>
                        <xsl:variable name="inst_pk"><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::pbcoreinstantiation.type_pk'))]/fmp:DATA[$pos]"/></xsl:variable>
                        <xsl:if test="$asset_fk=$asset_pk">
                            <pbcoreInstantiation>
                                <xsl:for-each select="../../fmp:COL[count(key('N', 'PBCoreFormatIdentifier::pbcoreinstantiation.type_fk'))]/fmp:DATA">
                                    <xsl:variable name="pos_formatid" select="position()"/>
                                    <xsl:variable name="inst_fk">
                                        <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreFormatIdentifier::pbcoreinstantiation.type_fk'))]/fmp:DATA[$pos_formatid]"/>
                                    </xsl:variable>
                                    <xsl:if test="$inst_pk=$inst_fk">
                                        <pbcoreFormatID>
                                            <formatIdentifier>
                                                <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreFormatIdentifier::formatIdentifier'))]/fmp:DATA[$pos_formatid]"/>
                                            </formatIdentifier>
                                            <formatIdentifierSource>
                                                <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreFormatIdentifier::formatIdentifierSource'))]/fmp:DATA[$pos_formatid]"/>
                                            </formatIdentifierSource>
                                        </pbcoreFormatID>
                                    </xsl:if>
                                </xsl:for-each>
                                <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreInstantiation::dateCreated'))]/fmp:DATA[$pos])>0">
                                    <dateCreated><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::dateCreated'))]/fmp:DATA[$pos]"/></dateCreated>
                                </xsl:if>
                                <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreInstantiation::dateIssued'))]/fmp:DATA[$pos])>0">
                                    <dateIssued><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::dateIssued'))]/fmp:DATA[$pos]"/></dateIssued>
                                </xsl:if>
                                <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreInstantiation::formatPhysical'))]/fmp:DATA[$pos])>0">
                                    <formatPhysical><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::formatPhysical'))]/fmp:DATA[$pos]"/></formatPhysical>
                                </xsl:if>
                                <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreInstantiation::formatDigital'))]/fmp:DATA[$pos])>0">
                                    <formatDigital><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::formatDigital'))]/fmp:DATA[$pos]"/></formatDigital>
                                </xsl:if>
                                <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreInstantiation::formatLocation'))]/fmp:DATA[$pos])>0">
                                    <formatLocation><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::formatLocation'))]/fmp:DATA[$pos]"/></formatLocation>
                                </xsl:if>
                                <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreInstantiation::alternativeModes'))]/fmp:DATA[$pos])>0">
                                    <alternativeModes><xsl:value-of select="../../fmp:COL[count(key('N','PBCoreInstantiation::formatTracks'))]/fmp:DATA[$pos]"/></alternativeModes>
                                </xsl:if>
                                <xsl:for-each select="../../fmp:COL[count(key('N', 'PBCoreEssenceTrack::pbcoreinstantiation.type_fk'))]/fmp:DATA">
                                    <xsl:variable name="pos_essTrack" select="position()"/>
                                    <xsl:variable name="inst_fk">
                                        <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreEssenceTrack::pbcoreinstantiation.type_fk'))]/fmp:DATA[$pos_essTrack]"/>
                                    </xsl:variable>
                                    <xsl:if test="$inst_pk=$inst_fk">
                                        <pbcoreEssenceTrack>
                                            <xsl:if test="string-length(../../fmp:COL[count(key('N','PBCoreEssenceTrack::essenceTrackType'))]/fmp:DATA[$pos_essTrack])>0">
                                                <essenceTrackType>
                                                    <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreEssenceTrack::essenceTrackType'))]/fmp:DATA[$pos_essTrack]"/>
                                                </essenceTrackType>
                                            </xsl:if>
                                        </pbcoreEssenceTrack>
                                    </xsl:if>
                                </xsl:for-each>
                                <xsl:for-each select="../../fmp:COL[count(key('N', 'PBCoreAnnotation::pbcoreinstantiation.type_fk'))]/fmp:DATA">
                                    <xsl:variable name="pos_ann" select="position()"/>
                                    <xsl:variable name="inst_fk">
                                        <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreAnnotation::pbcoreinstantiation.type_fk'))]/fmp:DATA[$pos_ann]"/>
                                    </xsl:variable>
                                    <xsl:if test="$inst_pk=$inst_fk">
                                        <pbcoreAnnotation>
                                            <annotation>
                                                <xsl:value-of select="../../fmp:COL[count(key('N','PBCoreAnnotation::annotation'))]/fmp:DATA[$pos_ann]"/>
                                            </annotation>
                                        </pbcoreAnnotation>
                                    </xsl:if>
                                </xsl:for-each>
                            </pbcoreInstantiation>
                        </xsl:if>
                    </xsl:for-each>
            </resource>
            </xsl:for-each>
        </resourceset>
    </xsl:template>
</xsl:stylesheet>
